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
from pathlib import Path
import sys

from django import db
from django.db import transaction
from django.core import serializers


from rdrf.helpers.utils import consent_check
from rdrf.models.definition.models import ConsentConfiguration, ConsentQuestion, ConsentSection, Registry
from rdrf.views.form_view import CustomConsentFormView
from registry.groups.models import CustomUser
from registry.patients.models import ConsentValue, Patient


ADMIN_USER = CustomUser.objects.get(username='admin')
ANGELMAN_REGISTRY = Registry.objects.get(code='ang')

MODELS_TO_BACKUP = (Patient, ConsentSection, ConsentQuestion, ConsentValue, ConsentConfiguration)

DATA_DIR = Path(__file__).parent / 'consent_migration_data'
CONSENT_SECTIONS_JSON = DATA_DIR / 'consent_sections.json'
CONSENT_QUESTIONS_JSON = DATA_DIR / 'consent_questions.json'
CONSENT_RULES_JSON = DATA_DIR / 'consent_rules.json'

# Now formatted in a file-name-friendly way. Ex. 20220411T092921Z for 11 Apr 2022 09:29:21 UTC
NOW = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

SAVED_CONSENTS_CSV = f'saved_patient_consents_{NOW}.csv'
MIGRATED_CONSENTS_CSV = f'migrated_patient_consents_{NOW}.csv'

BACKUP_DB_TABLE_PREFIX = 'BACKUP_'

NEW_CONSENT_SECTION_NAME = 'AngNewConsentSection'

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
    .filter(section__registry=ANGELMAN_REGISTRY)
    .order_by('section__code', 'position')
    .values_list('code', 'pk'))


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

    print_title('5. Saving migrated Patient consents to CSV file')
    save_migrated_patient_consents_to_csv_file(new_section)

    print_title('6. Delete old consent sections')
    delete_old_consents(new_section)

    print_title('7. Automated verification of migration')
    automated_verification(new_section)

    print('All done!')


def prevent_execution_if_already_executed_on_this_DB():
    if ConsentSection.objects.filter(code=NEW_CONSENT_SECTION_NAME).exists():
        print('Seems like the consent migration script was already executed on this Database.', file=sys.stderr)
        print('Refusing to execute!', file=sys.stderr)
        sys.exit(1)


def save_current_patient_consents_to_csv_file():
    _save_patient_consents_to_csv_file(SAVED_CONSENTS_CSV, questions_qs)


def save_migrated_patient_consents_to_csv_file(new_section):
    old_questions = list(questions_qs.exclude(section=new_section))
    new_questions = questions_qs.filter(section=new_section)

    questions = old_questions
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

    header = ['patient_id', 'is_active'] + [code for code, _ in questions]

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        patients = Patient.objects.really_all().filter(rdrf_registry=ANGELMAN_REGISTRY).prefetch_related('consents').order_by('pk')
        for patient in patients:
            values = {consent.consent_question_id: consent.answer for consent in patient.consents.all()}
            row = [patient.pk, patient.active] + [values.get(pk, '-') for pk in question_pks]
            writer.writerow(row)

    print_indented(f'Saved {len(patients)} Patients into {filename}.')


def make_copies_of_key_tables(models):
    db_tables = (m._meta.db_table for m in models)
    names = [(table_name, f'{BACKUP_DB_TABLE_PREFIX}_{table_name}_{NOW}') for table_name in db_tables]

    with db.connections['default'].cursor() as cursor:
        for name, backup_name in names:
            cursor.execute(f'CREATE TABLE {backup_name} AS TABLE {name}')

    print_indented('Created backup tables:')
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

    patients = Patient.objects.really_all().filter(rdrf_registry=ANGELMAN_REGISTRY).prefetch_related('consents', 'consents__consent_question').order_by('pk')

    consent_values_created = OrderedDict()
    for patient in patients:
        if not patient.consents.exists():
            consent_values_created[patient.pk] = []
            continue

        created = [migrate_mandatory_consents(patient, mandatory_question)]
        for from_question_code, new_question in new_questions:
            consent = migrate_optional_consent(patient, from_question_code, new_question)
            created.append(consent)
        consent_values_created[patient.pk] = [c for c in created if created is not None]

    total_created = sum(len(values) for values in consent_values_created.values())
    patient_count = len([v for v in consent_values_created.values() if v])
    print_indented(f'Created {total_created} Consent Values objects for {patient_count} of {len(patients)} Patients')

    return consent_values_created


def migrate_mandatory_consents(patient, mandatory_question):
    mandatory_consents = patient.consents.filter(consent_question__code__in=OLD_MANDATORY_CONSENTS)
    first_saves = [c.first_save for c in mandatory_consents if c.first_save]
    last_updates = [c.last_update for c in mandatory_consents if c.last_update]
    if mandatory_consents.count() == 0:
        return None
    expected_count = len(OLD_MANDATORY_CONSENTS)
    assert len(mandatory_consents) == expected_count, \
        f'Patient {patient.pk} has {len(mandatory_consents)} count instead of the expected {expected_count}'
    return ConsentValue.objects.create(
        patient=patient,
        consent_question=mandatory_question,
        answer=all(c.answer for c in mandatory_consents),
        first_save=min(first_saves) if first_saves else None,
        last_update=max(last_updates) if last_updates else None,
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
    total, details = (
        ConsentSection.objects
        .filter(registry=ANGELMAN_REGISTRY)
        .exclude(pk=new_section.pk)
        .delete())

    print_indented(f'Deleted a total of {total} objects:')
    for model, count in details.items():
        print_indented(f'- {model.split(".")[-1]}: {count}', indent=2)


def automated_verification(new_section):
    verify_consent_values_of_all_patients(new_section)
    verify_consent_based_form_access()


def verify_consent_values_of_all_patients(new_section):
    for patient, expected_values in _patient_expected_values(new_section):
        form, sections, *_ = CustomConsentFormView()._get_form_sections(ADMIN_USER, ANGELMAN_REGISTRY, patient)[0]
        assert len(sections) == 1, f'Form should display only 1 section (the new section) but it displays {len(sections)} sections!'
        section_name, field_keys = sections[0]

        assert section_name == new_section.section_label
        displayed_questions = [(form[k].label, form[k].value()) for k in field_keys]
        expected_questions = _apply_values(expected_values)
        assert len(displayed_questions) == len(expected_questions), \
            f'{len(expected_questions)} questions should be displayed not {len(displayed_questions)}!'
        for displayed, expected in zip(displayed_questions, expected_questions):
            assert displayed == expected, \
                f'Difference found for Patient with ID {patient.pk}:\n{displayed}\n{expected}'

    print_indented(f'Verified all patients in {SAVED_CONSENTS_CSV}.')


def verify_consent_based_form_access():
    consented = ConsentValue.objects.filter(consent_question__code=NEW_MANDATORY_CONSENT, patient__active=True).values_list('patient_id', flat=True)
    patient = Patient.objects.get(pk=consented[0])
    parent = patient.parentguardian_set.first()
    assert consent_check(ANGELMAN_REGISTRY, parent.user, patient, 'see_patient')

    patient = Patient.objects.exclude(pk__in=consented).first()
    parent = patient.parentguardian_set.first()
    assert not consent_check(ANGELMAN_REGISTRY, parent.user, patient, 'see_patient')

    print_indented('Verified consent based form access.')


def _patient_expected_values(new_section):
    migrated_questions = [NEW_MANDATORY_CONSENT] + [new for _, new in MIGRATE_QUESTION_FROM_TO]
    new_questions = set(q.code for q in new_section.questions.all() if q.code not in migrated_questions)

    def expected_values(row):
        expected = {new: row[old] == 'True' for old, new in MIGRATE_QUESTION_FROM_TO}
        expected[NEW_MANDATORY_CONSENT] = all(row[code] == 'True' for code in OLD_MANDATORY_CONSENTS)
        expected.update({q: False for q in new_questions})

        return expected

    with open(SAVED_CONSENTS_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield Patient.objects.really_all().get(pk=row['patient_id']), expected_values(row)


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
    print(' ' * 4 * indent + str(s))


# Used for the verification step, to assert the text and the values being displayed after the
# migration finished.
# The order of the questions is important and the text and New codes have been copied here directly *
# from the Wiki page to make the assertions process better.
#
#    * Some questions had no . ending the sentence on the Wiki page.
#      Added the missing .'s to make all questions consistent.
#
# Ref: https://eresearchqut.atlassian.net/wiki/spaces/ERS/pages/1682702345/Angelman+Consent+Migration
#
# ie. the duplication between this and the JSON files importing the questions is intentional!
NEW_CONSENT_SECTION_QUESTIONS_TEMPLATE = (
    ('1. I confirm that I have read and understood the above information sheet (V10.7) dated '
     '1 February 2022. I have had the opportunity to think about the information, ask questions, '
     'and have had questions answered to my satisfaction.',
     'angnewconsent1'),
    ('2. I confirm that I am happy for the nominated specialist in charge of my medical care '
     'to be contacted if required.',
     'angnewconsent3b'),
    ('3. I confirm that I am happy for my de-identified data to be made available for analysis '
     'through third party platforms or researchers.',
     'angnewconsent4b'),
    ('4. I consent to being contacted to complete additional modules for longitudinal follow up.',
     'angnewconsent6b'),
    ('5. I consent to being contacted about clinical trials and research studies that my child/ '
     'adult with Angelman Syndrome may be eligible to participate in.',
     'angnewconsent2'),
    ('6. I consent to being contacted about opportunities to connect with Angelman organisations if '
     'there is an opportunity to do so.',
     'angnewconsent5b'),
)


def _apply_values(expected_values):
    return [(text, expected_values[value]) for text, value in NEW_CONSENT_SECTION_QUESTIONS_TEMPLATE]
