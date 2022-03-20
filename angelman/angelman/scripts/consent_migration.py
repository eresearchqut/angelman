"""
Script that migrates old consents in Angelman to new consents.

To be executed with:

django-admin runscript consent_migration

Creates CSV files during execution:

    - saved_patient_consents_TIMESTAMP.csv - consents of all patients saved before touching the data
    - migrated_patient_consents_TIMESTAMP.csv - old and new consents of all patients after migration

Each column is the ConsentValue.answer (True or False) of the ConsentQuestion. '-' indicates no 
ConsentValue exists for the given question.

The migrated patient consents CSV columns are ordered so that new questions are right after their
corresponding old questions (the questions they've been migrated from) for easier inspection.
"""
from collections import OrderedDict
import csv
from datetime import datetime
from functools import partial
from pathlib import Path
import sys

from django import db
from django.db import transaction
from django.core import serializers


from rdrf.models.definition.models import ConsentConfiguration, ConsentQuestion, ConsentSection
from registry.patients.models import ConsentValue, Patient


REGISTRY_CODE = 'ang'
MODELS_TO_BACKUP = (Patient, ConsentSection, ConsentQuestion, ConsentValue, ConsentConfiguration)

DATA_DIR = Path(__file__).parent / 'consent_migration_data'
CONSENT_SECTIONS_JSON = DATA_DIR / 'consent_sections.json'
CONSENT_QUESTIONS_JSON = DATA_DIR / 'consent_questions.json'
CONSENT_RULES_JSON = DATA_DIR / 'consent_rules.json'

# Now formatted in a file-name-friendly way
NOW = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

SAVED_CONSENTS_CSV = f'saved_patient_consents_{NOW}.csv'
MIGRATED_CONSENTS_CSV = f'migrated_patient_consents_{NOW}.csv'


OLD_MANDATORY_CONSENTS = (
    'angconsent1', 'angconsent2', 'angconsent3', 'angconsent4',
    'angconsent5', 'angconsent6', 'angconsent7', 'angconsent8')
NEW_MANDATORY_CONSENT = 'angnewconsent1'

MIGRATE_QUESTION_FROM_TO = (
    ('angconsent9', 'angnewconsent3b'),
    ('angconsentTRANSMART', 'angnewconsent4b'),
    ('angconsent10', 'angnewconsent6b'),
    ('angconsent11', 'angnewconsent2'),
)

questions_qs = (
    ConsentQuestion.objects
    .filter(section__registry__code=REGISTRY_CODE)
    .order_by('section__code', 'position')
    .values_list('code', 'pk'))


# TODO 
#   - (LOCAL) more testing:
#        reimport angelman yaml, enter test data based on PROD, export zip, re-test script
#   - historical records?
#   - we don't have clinicians in Angelman, right? (Important only if we do check ConsentQuestion.create_field)
#   - automated tests:
#        As the last step,

#        for each Patient in SAVED_CONSENTS_CSV:
#            Determine what the new consent answers should be based on the rules.
#            Then verify them by:
#
#            ccfv =rdrf.views.form_view.CustomConsentFormView()
#            form, sections = _get_form_sections(USER, angelman_registry, patient)
#
#            You could do this test several times, for key USERs: ie. admin, curator, parent/patient
#
#     sections is a list of (section name, [field_keys])
#     it should have just the one section we created
#     form[field_key] is the BoundBooleanField so use .label  and .value() (True/False)
#     to get the question text and whether the checkbox is checked or not on the consent form for the patient


@transaction.atomic
def run():
    print_title('1. Saving current Patient consents to CSV file')
    save_current_patient_consents_to_csv_file()

    prevent_execution_if_already_executed_on_this_DB()

    print_title('2. Backing up tables')
    make_copies_of_key_tables(MODELS_TO_BACKUP)

    print_title('3. Creating new consent section and questions')
    new_section = create_new_consent_section_questions_and_rules()

    print_title('4. Migrating old consents into new consents')
    migrate_old_consents_into_new_consents()

    assert False, 'bum'

    print_title('5. Saving migrated Patient consents to CSV file')
    save_migrated_patient_consents_to_csv_file(new_section)

    print_title('6. Delete old consent sections')
    delete_old_consents(new_section)

    print('All done!')


def prevent_execution_if_already_executed_on_this_DB():
    if ConsentSection.objects.filter(code='AngNewConsentSection').exists():
        print('Seems like the consent migration script was already executed on this Database.', file=sys.stderr)
        print('Refusing to execute!', file=sys.stderr)
        sys.exit(1)


def save_current_patient_consents_to_csv_file():
    _save_patient_consents_to_csv_file(SAVED_CONSENTS_CSV, questions_qs)


def save_migrated_patient_consents_to_csv_file(new_section):
    old_questions = list(questions_qs.exclude(section=new_section))
    new_questions = questions_qs.filter(section=new_section)

    questions = old_questions[:]
    insert_after_question = {to: from_ for from_, to in MIGRATE_QUESTION_FROM_TO}
    insert_after_question[NEW_MANDATORY_CONSENT] = OLD_MANDATORY_CONSENTS[-1]

    def find_insertion_point(questions, insert_after):
        if insert_after is None:
            return len(questions)
        for i, q in enumerate(questions):
            if insert_after == q[0]:
                return i + 1
        
    # Ordering questions so that each new question comes right after the old question they've been migrated from
    for code, pk in new_questions:
        index = find_insertion_point(questions, insert_after_question.get(code))
        questions.insert(index, (code, pk))
    
    _save_patient_consents_to_csv_file(MIGRATED_CONSENTS_CSV, questions)


def _save_patient_consents_to_csv_file(filename, questions):
    question_pks = [pk for _, pk in questions]

    header = ['patient_id'] + [code for code, _ in questions]

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        patients = Patient.objects.filter(rdrf_registry__code=REGISTRY_CODE).prefetch_related('consents').order_by('pk')
        for patient in patients:
            values = {consent.consent_question_id: consent.answer for consent in patient.consents.all()}
            row = [patient.pk] + [values.get(pk, '-') for pk in question_pks] 
            writer.writerow(row)

    print_indented(f'Saved {len(patients)} Patients into {filename}.')


def make_copies_of_key_tables(models):
    db_tables = (m._meta.db_table for m in models)
    names = [(table_name, '_'.join((table_name, NOW))) for table_name in db_tables]

    with db.connections['default'].cursor() as cursor:
        for name, backup_name in names:
            pass
            # TODO re-enable
            # cursor.execute(f'CREATE TABLE {backup_name} AS TABLE {name}')

    print_indented(f'Created backup tables:')
    for _, n in names:
        print_indented(n, indent=2)
    return names


def create_new_consent_section_questions_and_rules():
    section = _deserialize_and_save(CONSENT_SECTIONS_JSON)[0]
    print_indented(f'Created section: {section} ({section.code})')
    questions = _deserialize_and_save(CONSENT_QUESTIONS_JSON) 
    print_indented(f'Created {len(questions)} questions:')
    for q in questions:
        print_indented(f'- {q.code}', indent=2)
    rules = _deserialize_and_save(CONSENT_RULES_JSON) 
    print_indented(f'Created {len(rules)} consent rules.')


    return section


def migrate_old_consents_into_new_consents():
    mandatory_question = ConsentQuestion.objects.get(code=NEW_MANDATORY_CONSENT)
    new_questions = [(from_, ConsentQuestion.objects.get(code=to)) for from_, to in MIGRATE_QUESTION_FROM_TO]

    patients = Patient.objects.filter(rdrf_registry__code=REGISTRY_CODE).prefetch_related('consents', 'consents__consent_question').order_by('pk')

    consent_values_created = OrderedDict()
    for patient in patients:
        created = []
        consent_values_created[patient.pk] = created

        consents = patient.consents
        if not consents.exists():
            continue

        consent = migrate_mandatory_consents(patient, mandatory_question)
        created.append(consent)
        for from_question_code, new_question in new_questions:
            consent = migrate_optional_consent(patient, from_question_code, new_question)
            created.append(consent)
        created = [c for c in created if created is not None]

    total_created = sum(len(values) for values in consent_values_created.values())
    patient_count = len([v for v in consent_values_created.values() if v])
    print_indented(f'Created {total_created} Consent Values objects for {patient_count} of {len(patients)} Patients')

    return consent_values_created


def migrate_mandatory_consents(patient, mandatory_question):
    mandatory_consents = patient.consents.filter(consent_question__code__in=OLD_MANDATORY_CONSENTS)
    first_saves = [c.first_save for c in mandatory_consents if c.first_save]
    last_updates = [c.last_update for c in mandatory_consents if c.last_update]
    if len(mandatory_consents) == len(OLD_MANDATORY_CONSENTS):
        return ConsentValue.objects.create(
                patient=patient,
                consent_question=mandatory_question,
                answer=all(c.answer for c in mandatory_consents),
                first_save=min(first_saves) if first_saves else None,
                last_update=max(last_updates) if last_updates else None,
                # TODO do we do something about history (HistoricalRecords)
            )


def migrate_optional_consent(patient, from_question_code, new_question):
    consent_value = patient.consents.filter(consent_question__code=from_question_code).first()
    if consent_value is None:
        return
    consent_value.pk = None
    consent_value.consent_question = new_question
    consent_value.save()
    return consent_value


def delete_old_consents(new_section):
    # TODO re-enable
    print('Re-enable!')
    return
    total, details = (
        ConsentSection.objects
        .filter(registry__code=REGISTRY_CODE)
        .exclude(pk=new_section.pk)
        .delete())

    print_indented(f'Deleted a total of {total} objects:')
    for model, count in details.items():
        print_indented(f'- {model.split(".")[-1]}: {count}', indent=2)


def _deserialize_and_save(filename):
    with open(DATA_DIR / filename) as f:
        models = [dobj.object for dobj in serializers.deserialize('json', f)]
        # Note: saving the DeserializedObject.object instead of the DeserializedObject
        # to have created_at and last_updated_at set correctly (they would be None otherwise)
        for m in models:
            m.save()
        return models


def print_title(title):
    print()
    print(title)
    print('=' * len(title))


def print_indented(s, indent=1):
    print(' ' * 4 * indent + s)

