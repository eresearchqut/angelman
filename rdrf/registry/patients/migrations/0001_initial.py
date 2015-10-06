# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AddressType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=100)),
                ('description', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConsentValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.BooleanField(default=False)),
                ('first_save', models.DateField(null=True, blank=True)),
                ('last_update', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('family_name', models.CharField(max_length=100, db_index=True)),
                ('given_names', models.CharField(max_length=100, db_index=True)),
                ('surgery_name', models.CharField(max_length=100, blank=True)),
                ('speciality', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('suburb', models.CharField(max_length=50, verbose_name=b'Suburb/Town')),
                ('phone', models.CharField(max_length=30, null=True, blank=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
            ],
            options={
                'ordering': ['family_name'],
            },
        ),
        migrations.CreateModel(
            name='NextOfKinRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(max_length=100, verbose_name=b'Relationship')),
            ],
            options={
                'verbose_name': 'Next of Kin Relationship',
            },
        ),
        migrations.CreateModel(
            name='ParentGuardian',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=50)),
                ('date_of_birth', models.DateField(null=True, blank=True)),
                ('place_of_birth', models.CharField(max_length=100, null=True, verbose_name=b'Place of birth', blank=True)),
                ('date_of_migration', models.DateField(null=True, blank=True)),
                ('gender', models.CharField(max_length=1, choices=[(b'M', b'Male'), (b'F', b'Female')])),
                ('address', models.TextField()),
                ('suburb', models.CharField(max_length=50, verbose_name=b'Suburb/Town')),
                ('state', models.CharField(max_length=20, verbose_name=b'State/Province/Territory')),
                ('postcode', models.CharField(max_length=20, blank=True)),
                ('country', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('consent', models.BooleanField(help_text=b'The patient consents to be part of the registry and have data retained and shared in accordance with the information provided to them.', verbose_name=b'consent given')),
                ('consent_clinical_trials', models.BooleanField(default=False, help_text=b'Consent given to be contacted about clinical trials or other studies related to their condition.')),
                ('consent_sent_information', models.BooleanField(default=False, help_text=b'Consent given to be sent information on their condition', verbose_name=b'consent to be sent information given')),
                ('consent_provided_by_parent_guardian', models.BooleanField(default=False, help_text=b'Parent/Guardian consent provided on behalf of the patient.')),
                ('family_name', models.CharField(max_length=100, db_index=True)),
                ('given_names', models.CharField(max_length=100, db_index=True)),
                ('maiden_name', models.CharField(max_length=100, null=True, verbose_name=b'Maiden Name (if applicable)', blank=True)),
                ('umrn', models.CharField(db_index=True, max_length=50, null=True, verbose_name=b'Hospital/Clinic ID', blank=True)),
                ('date_of_birth', models.DateField()),
                ('place_of_birth', models.CharField(max_length=100, null=True, verbose_name=b'Place of birth', blank=True)),
                ('country_of_birth', models.CharField(max_length=100, null=True, verbose_name=b'Country of birth', blank=True)),
                ('ethnic_origin', models.CharField(blank=True, max_length=100, null=True, choices=[(b'New Zealand European', b'New Zealand European'), (b'Australian', b'Australian'), (b'Other Caucasian/European', b'Other Caucasian/European'), (b'Aboriginal', b'Aboriginal'), (b'Person from the Torres Strait Islands', b'Person from the Torres Strait Islands'), (b'Maori', b'Maori'), (b'NZ European / Maori', b'NZ European / Maori'), (b'Samoan', b'Samoan'), (b'Cook Islands Maori', b'Cook Islands Maori'), (b'Tongan', b'Tongan'), (b'Niuean', b'Niuean'), (b'Tokelauan', b'Tokelauan'), (b'Fijian', b'Fijian'), (b'Other Pacific Peoples', b'Other Pacific Peoples'), (b'Southeast Asian', b'Southeast Asian'), (b'Chinese', b'Chinese'), (b'Indian', b'Indian'), (b'Other Asian', b'Other Asian'), (b'Middle Eastern', b'Middle Eastern'), (b'Latin American', b'Latin American'), (b'Black African/African American', b'Black African/African American'), (b'Other Ethnicity', b'Other Ethnicity'), (b'Decline to Answer', b'Decline to Answer')])),
                ('sex', models.CharField(max_length=1, choices=[(b'1', b'Male'), (b'2', b'Female'), (b'3', b'Indeterminate')])),
                ('home_phone', models.CharField(max_length=30, null=True, blank=True)),
                ('mobile_phone', models.CharField(max_length=30, null=True, blank=True)),
                ('work_phone', models.CharField(max_length=30, null=True, blank=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('next_of_kin_family_name', models.CharField(max_length=100, null=True, verbose_name=b'family name', blank=True)),
                ('next_of_kin_given_names', models.CharField(max_length=100, null=True, verbose_name=b'given names', blank=True)),
                ('next_of_kin_address', models.TextField(null=True, verbose_name=b'Address', blank=True)),
                ('next_of_kin_suburb', models.CharField(max_length=50, null=True, verbose_name=b'Suburb/Town', blank=True)),
                ('next_of_kin_state', models.CharField(max_length=20, null=True, verbose_name=b'State/Province/Territory', blank=True)),
                ('next_of_kin_postcode', models.IntegerField(null=True, verbose_name=b'Postcode', blank=True)),
                ('next_of_kin_home_phone', models.CharField(max_length=30, null=True, verbose_name=b'home phone', blank=True)),
                ('next_of_kin_mobile_phone', models.CharField(max_length=30, null=True, verbose_name=b'mobile phone', blank=True)),
                ('next_of_kin_work_phone', models.CharField(max_length=30, null=True, verbose_name=b'work phone', blank=True)),
                ('next_of_kin_email', models.EmailField(max_length=254, null=True, verbose_name=b'email', blank=True)),
                ('next_of_kin_parent_place_of_birth', models.CharField(max_length=100, null=True, verbose_name=b'Place of birth of parents', blank=True)),
                ('next_of_kin_country', models.CharField(max_length=100, null=True, verbose_name=b'Country', blank=True)),
                ('active', models.BooleanField(default=True, help_text=b'Ticked if active in the registry, ie not a deleted record, or deceased patient.')),
                ('inactive_reason', models.TextField(help_text=b'Please provide reason for deactivating the patient', null=True, verbose_name=b'Reason', blank=True)),
                ('clinician', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['family_name', 'given_names', 'date_of_birth'],
                'verbose_name_plural': 'Patient List',
                'permissions': (('can_see_full_name', 'Can see Full Name column'), ('can_see_dob', 'Can see Date of Birth column'), ('can_see_working_groups', 'Can see Working Groups column'), ('can_see_diagnosis_progress', 'Can see Diagnosis Progress column'), ('can_see_diagnosis_currency', 'Can see Diagnosis Currency column'), ('can_see_genetic_data_map', 'Can see Genetic Module column'), ('can_see_data_modules', 'Can see Data Modules column')),
            },
        ),
        migrations.CreateModel(
            name='PatientAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.TextField()),
                ('suburb', models.CharField(max_length=100, verbose_name=b'Suburb/Town')),
                ('state', models.CharField(max_length=50, verbose_name=b'State/Province/Territory')),
                ('postcode', models.CharField(max_length=50)),
                ('country', models.CharField(max_length=100)),
                ('address_type', models.ForeignKey(default=1, to='patients.AddressType')),
                ('patient', models.ForeignKey(to='patients.Patient')),
            ],
            options={
                'verbose_name_plural': 'Patient Addresses',
            },
        ),
        migrations.CreateModel(
            name='PatientConsent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('form', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/static/media/', location=b'/data/static/media'), upload_to=b'consents', null=True, verbose_name=b'Consent form', blank=True)),
                ('patient', models.ForeignKey(to='patients.Patient')),
            ],
        ),
        migrations.CreateModel(
            name='PatientDoctor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relationship', models.CharField(max_length=50)),
                ('doctor', models.ForeignKey(to='patients.Doctor')),
                ('patient', models.ForeignKey(to='patients.Patient')),
            ],
            options={
                'verbose_name': 'medical professionals for patient',
                'verbose_name_plural': 'medical professionals for patient',
            },
        ),
        migrations.CreateModel(
            name='PatientRelative',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('family_name', models.CharField(max_length=100)),
                ('given_names', models.CharField(max_length=100)),
                ('date_of_birth', models.DateField()),
                ('sex', models.CharField(max_length=1, choices=[(b'M', b'Male'), (b'F', b'Female'), (b'X', b'Other/Intersex')])),
                ('relationship', models.CharField(max_length=80, choices=[(b'Parent', b'Parent'), (b'Sibling', b'Sibling'), (b'Child', b'Child'), (b'Identical Twin', b'Identical Twin'), (b'Half Sibling', b'Half Sibling'), (b'Niece/Nephew', b'Niece/Nephew'), (b'1st Cousin', b'1st Cousin'), (b'Grandchild', b'Grandchild'), (b'Uncle/Aunty', b'Uncle/Aunty'), (b'Spouse', b'Spouse'), (b'Non-identical twin', b'Non-identical twin'), (b'Grandparent', b'Grandparent'), (b'1st cousin once removed', b'1st cousin once removed'), (b'Great Grandparent', b'Great Grandparent'), (b'Great Grandchild', b'Great Grandchild'), (b'Great Uncle/Aunt', b'Great Uncle/Aunt'), (b'Great Niece/Nephew', b'Great Niece/Nephew'), (b'Unknown', b'Unknown'), (b'Other', b'Other')])),
                ('location', models.CharField(max_length=80, choices=[(b'AU - WA', b'Australia - WA'), (b'AU - SA', b'Australia - SA'), (b'AU - NSW', b'Australia - NSW'), (b'AU - QLD', b'Australia - QLD'), (b'AU - NT', b'Australia - NT'), (b'AU - VIC', b'Australia - VIC'), (b'AU - TAS', b'Australia - TAS'), (b'NZ', b'New Zealand'), ('AF', 'Afghanistan'), ('AX', '\xc5land Islands'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo, The Democratic Republic of the'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('CI', "C\xf4te d'Ivoire"), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands (Malvinas)'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See (Vatican City State)'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran, Islamic Republic of'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea, Democratic People's Republic of"), ('KR', 'Korea, Republic of'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia, Republic of'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia, Federated States of'), ('MD', 'Moldova, Republic of'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RE', 'R\xe9union'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SS', 'South Sudan'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan, Province of China'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands, British'), ('VI', 'Virgin Islands, U.S.'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe')])),
                ('living_status', models.CharField(max_length=80, choices=[(b'Alive', b'Living'), (b'Deceased', b'Deceased')])),
                ('patient', models.ForeignKey(related_name='relatives', to='patients.Patient')),
                ('relative_patient', models.OneToOneField(related_name='as_a_relative', null=True, blank=True, to='patients.Patient', verbose_name=b'Create Patient?')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('short_name', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('country_code', models.CharField(max_length=30, null=True, blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='patient',
            name='doctors',
            field=models.ManyToManyField(to='patients.Doctor', through='patients.PatientDoctor'),
        ),
        migrations.AddField(
            model_name='patient',
            name='next_of_kin_relationship',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Relationship', blank=True, to='patients.NextOfKinRelationship', null=True),
        ),
    ]
