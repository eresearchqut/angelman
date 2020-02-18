import logging

from django.utils.translation import get_language

from rdrf.events.events import EventType
from rdrf.models.workflow_models import ClinicianSignupRequest
from rdrf.services.io.notifications.email_notification import process_notification

from registration.models import RegistrationProfile
from registry.patients.models import ParentGuardian, Patient, PatientAddress, AddressType
from registry.groups import GROUPS


from registry.groups.registration.base import BaseRegistration


logger = logging.getLogger(__name__)


class AngelmanRegistration(BaseRegistration):

    def __init__(self, request, form):
        super().__init__(request, form)
        self.token = request.session.get("token", None)
        self.request = request
        if self.token:
            try:
                self.clinician_signup = ClinicianSignupRequest.objects.get(token=self.token,
                                                                           state="emailed")
            except ClinicianSignupRequest.DoesNotExist:
                raise Exception("Clinician already signed up or unknown token")
        else:
            self.clinician_signup = None

    def _do_clinician_signup(self, registry_model):
        from rdrf.helpers.utils import get_site
        user = self._create_django_user(self.request,
                                        self.user,
                                        registry_model,
                                        is_parent=False,
                                        is_clinician=True)

        logger.debug("created django user for clinician")

        # working group should be the working group of the patient
        patient = Patient.objects.get(id=self.clinician_signup.patient_id)

        user.working_groups.set([wg for wg in patient.working_groups.all()])
        user.save()
        logger.debug("set clinician working groups to patient's")
        self.clinician_signup.clinician_other.user = user
        self.clinician_signup.clinician_other.use_other = False
        self.clinician_signup.clinician_other.save()
        self.clinician_signup.state = "signed-up"   # at this stage the user is created but not active
        self.clinician_signup.save()
        patient.clinician = user
        patient.save()
        logger.debug("made this clinician the clinician of the patient")

        site_url = get_site()

        activation_template_data = {
            "site_url": site_url,
            "clinician_email": self.clinician_signup.clinician_email,
            "clinician_lastname": self.clinician_signup.clinician_other.clinician_last_name,
            "registration": RegistrationProfile.objects.get(user=user)
        }

        process_notification(registry_model.code,
                             EventType.CLINICIAN_ACTIVATION,
                             activation_template_data)
        logger.debug("AngelmanRegistration process - sent activation link for registered clinician")

    def process(self, user):
        registry_code = self.form.cleaned_data['registry_code']
        registry = self._get_registry_object(registry_code)

        if self.clinician_signup:
            logger.debug("signing up clinician")
            self._do_clinician_signup(registry)
            return

        user = self.update_django_user(user, registry)

        working_group = self._get_unallocated_working_group(registry)
        user.working_groups.set([working_group])
        user.save()

        logger.debug("Registration process - created user")
        patient = self._create_patient(registry, working_group, user, set_link_to_user=False)
        logger.debug("Registration process - created patient")
        patient.home_phone = self.form.cleaned_data["phone_number"]
        patient.save(update_fields=['home_phone'])

        address = self._create_patient_address(patient)
        address.save()
        logger.debug("Registration process - created patient address")

        parent_guardian = self._create_parent()

        parent_guardian.patient.add(patient)
        parent_guardian.user = user
        parent_guardian.save()
        logger.debug("Registration process - created parent")

        template_data = {
            "patient": patient,
            "parent": parent_guardian,
            "registration": RegistrationProfile.objects.get(user=user)
        }

        process_notification(registry_code, EventType.NEW_PATIENT, template_data)
        logger.debug("Registration process - sent notification for NEW_PATIENT")

    def _create_patient_address(self, patient, address_type="Postal"):
        form_data = self.form.cleaned_data
        same_address = form_data.get("same_address", False)
        return PatientAddress.objects.create(
            patient=patient,
            address_type=self.get_address_type(address_type),
            address=form_data["parent_guardian_address"] if same_address else form_data["address"],
            suburb=form_data["parent_guardian_suburb"] if same_address else form_data["suburb"],
            state=form_data["parent_guardian_state"] if same_address else form_data["state"],
            postcode=form_data["parent_guardian_postcode"] if same_address else form_data["postcode"],
            country=form_data["parent_guardian_country"] if same_address else form_data["country"]
        )

    def get_address_type(self, address_type):
        address_type_obj, created = AddressType.objects.get_or_create(type=address_type)
        return address_type_obj

    def _create_parent(self):
        form_data = self.form.cleaned_data
        parent_guardian = ParentGuardian.objects.create(
            first_name=form_data["parent_guardian_first_name"],
            last_name=form_data["parent_guardian_last_name"],
            date_of_birth=form_data["parent_guardian_date_of_birth"],
            gender=form_data["parent_guardian_gender"],
            address=form_data["parent_guardian_address"],
            suburb=form_data["parent_guardian_suburb"],
            state=form_data["parent_guardian_state"],
            postcode=form_data["parent_guardian_postcode"],
            country=form_data["parent_guardian_country"],
            phone=form_data["parent_guardian_phone"],
        )
        return parent_guardian

    def update_django_user(self, django_user, registry):
        form_data = self.form.cleaned_data
        first_name = form_data['parent_guardian_first_name']
        last_name = form_data['parent_guardian_last_name']

        preferred_language = self.form.cleaned_data.get('preferred_language', 'en')
        django_user.preferred_language = preferred_language

        return self.setup_django_user(django_user, registry, GROUPS.PARENT, first_name, last_name)

    @property
    def language(self):
        return get_language()

    def get_template_name(self):
        return "registration/registration_form.html"
