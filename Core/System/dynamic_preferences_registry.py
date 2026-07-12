from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry 
from dynamic_preferences.types import  StringPreference, BooleanPreference, FilePreference, LongStringPreference,ChoicePreference

# from Core.System.views import Maintenance_On, Maintenance_Off
sendemail = Section('SMTP')
sendsms = Section('SMS')
company = Section('COMPANY')
devloper = Section('DEVLOPER')
thirdparty = Section('THIRDPARTY')
customerapp = Section('CUSTOMERAPP')
deliveryapp = Section('DELIVERYAPP')
jsonpushfile = Section('JSON_DATA')



@global_preferences_registry.register
class HostUser(StringPreference):
    section = sendemail
    name = 'USER'
    default = 'adityaabsolin@gmail.com'
    required = True
    verbose_name ='HOST_USER'


@global_preferences_registry.register
class Password(StringPreference):
    section = sendemail
    name = 'PASSWORD'
    default = ''
    required = True
    verbose_name ='PASSWORD'


@global_preferences_registry.register
class Port(StringPreference):
    section = sendemail
    name = 'PORT'
    default = '587'
    required = True
    verbose_name ='PORT'


@global_preferences_registry.register
class Tls(BooleanPreference):
    section = sendemail
    name = 'USE_TLS'
    default = True
    required = True
    verbose_name ='TLS'


@global_preferences_registry.register
class EmailHost(StringPreference):
    section = sendemail
    name = 'HOST'
    default = 'smtp.gmail.com'
    required = True
    verbose_name ='EMAIL_HOST'


@global_preferences_registry.register
class EmailBackend(StringPreference):
    section = sendemail
    name = 'BACKEND'
    default = 'django.core.mail.backends.smtp.EmailBackend'
    required = True
    verbose_name ='EMAIL_BACKEND'


@global_preferences_registry.register
class Url(StringPreference):
    section = sendsms
    name = 'URL'
    default = ''
    required = True
    verbose_name ='URL'


@global_preferences_registry.register
class Message(StringPreference):
    section = sendsms
    name = 'MSG_VAR'
    default = ''
    required = True
    verbose_name ='MSG_VAR'


@global_preferences_registry.register
class Number(StringPreference):
    section = sendsms
    name = 'NUMBER_VAR'
    default = ''
    required = True
    verbose_name ='NUMBER_VAR'

@global_preferences_registry.register
class EnableSMS(ChoicePreference):
    choices = [
                ('T', 'TRUE'),
                ('F', 'FALSE'),
            ]
    section = sendsms
    name = 'ENABLE_SMS'
    default = ''
    required = True
    verbose_name ='ENABLE_SMS'

@global_preferences_registry.register
class Logo(FilePreference):
    section = company
    name = 'LOGO'
    default = ''
    required = True
    verbose_name ='LOGO'


@global_preferences_registry.register
class SmallLogo(FilePreference):
    section = company
    name = 'SMALLLOGO'
    default = ''
    required = True
    verbose_name ='SMALLLOGO'


@global_preferences_registry.register
class Name(StringPreference):
    section = company
    name = 'NAME'
    default = ''
    required = True
    verbose_name ='NAME'


@global_preferences_registry.register
class SimpleName(StringPreference):
    section = company
    name = 'SIMPLENAME'
    default = ''
    required = True
    verbose_name ='SIMPLENAME'


@global_preferences_registry.register
class Email(StringPreference):
    section = company
    name = 'EMAIL'
    default = ''
    required = True
    verbose_name ='EMAIL'


@global_preferences_registry.register
class Mobile(StringPreference):
    section = company
    name = 'MOBILE'
    default = ''
    required = True
    verbose_name ='MOBILE'


@global_preferences_registry.register
class AlternateMobile(StringPreference):
    section = company
    name = 'ALTERNATEMOBILE'
    default = ''
    required = False
    verbose_name ='ALTERNATEMOBILE'



@global_preferences_registry.register
class Website(StringPreference):
    section = company
    name = 'WEBSITE'
    default = ''
    required = True
    verbose_name ='WEBSITE'


@global_preferences_registry.register
class GstNo(StringPreference):
    section = company
    name = 'GSTNO'
    default = ''
    required = True
    verbose_name ='GSTNO'


@global_preferences_registry.register
class Address(LongStringPreference):
    section = company
    name = 'ADDRESS'
    default = ''
    required = True
    verbose_name ='ADDRESS'


@global_preferences_registry.register
class Email(StringPreference):
    section = devloper
    name = 'EMAIL'
    default = ''
    required = True
    verbose_name ='EMAIL'


@global_preferences_registry.register
class Mobile(StringPreference):
    section = devloper
    name = 'MOBILE'
    default = ''
    required = True
    verbose_name ='MOBILE'



@global_preferences_registry.register
class MaintenanceMode(BooleanPreference):
    section = devloper
    name = 'MAINTENANCEMODE'
    default = False
    required = True
    verbose_name ='Maintenance Mode'



@global_preferences_registry.register
class Url(StringPreference):
    section = thirdparty
    name = 'URL'
    default = ''
    required = True
    verbose_name ='URL'



@global_preferences_registry.register
class Token(StringPreference):
    section = thirdparty
    name = 'TOKEN'
    default = ''
    required = True
    verbose_name ='TOKEN'


@global_preferences_registry.register
class HelplinePhone(StringPreference):
    section = customerapp
    name = 'HELPLINEPHONE'
    default = ''
    required = True
    verbose_name ='HELPLINEPHONE'


@global_preferences_registry.register
class HelplineEmail(StringPreference):
    section = customerapp
    name = 'HELPLINEEMAIL'
    default = ''
    required = True
    verbose_name ='HELPLINEEMAIL'



@global_preferences_registry.register
class MaximumDeliveryDays(StringPreference):
    section = customerapp
    name = 'MAXIMUMDELIVERYDAYS'
    default = ''
    required = True
    verbose_name ='MAXIMUMDELIVERYDAYS'


@global_preferences_registry.register
class CutOffTime(StringPreference):
    section = customerapp
    name = 'CUTOFFTIME'
    default = ''
    required = True
    verbose_name ='CUTOFFTIME'


@global_preferences_registry.register
class RecentOrderDeactivateCount(StringPreference):
    section = customerapp
    name = 'RECENTORDERDEACTIVATECOUNT'
    default = '0'
    required = True
    verbose_name ='RECENTORDERDEACTIVATECOUNT'


@global_preferences_registry.register
class DeliveryManager(StringPreference):
    section = deliveryapp
    name = 'MOBILENUMBER'
    default = ''
    required = True
    verbose_name ='MOBILENUMBER'


@global_preferences_registry.register
class JsonData(StringPreference):
    section = jsonpushfile
    name = 'JSONFILE'
    default = '{}'
    required = True
    verbose_name ='JSONFILE'


@global_preferences_registry.register
class EnableAutoSync(ChoicePreference):
    choices = [
                ('T', 'TRUE'),
                ('F', 'FALSE'),
            ]
    section = thirdparty
    name = 'ENABLE_AUTOSYNC'
    default = ''
    required = True
    verbose_name ='ENABLE_AUTOSYNC'


@global_preferences_registry.register
class AMCUEnableAutoSync(ChoicePreference):
    choices = [
                ('T', 'TRUE'),
                ('F', 'FALSE'),
            ]
    section = thirdparty
    name = 'AMCU_ENABLE_AUTOSYNC'
    default = ''
    required = True
    verbose_name ='AMCU_ENABLE_AUTOSYNC'


@global_preferences_registry.register
class FocusSyncOn(ChoicePreference):
    choices = [
                ('T', 'TRUE'),
                ('F', 'FALSE'),
            ]
    section = thirdparty
    name = 'FOCUS_SYNC_ON'
    default = ''
    required = True
    verbose_name ='FOCUS_SYNC_ON'


@global_preferences_registry.register
class FocusBaseUrl(StringPreference):
    section = thirdparty
    name = 'FOCUS_BASEURL'
    default = ''
    required = True
    verbose_name ='FOCUS_BASEURL'


@global_preferences_registry.register
class FocusCompanyCode(StringPreference):
    section = thirdparty
    name = 'FOCUS_COMPANY_CODE'
    default = ''
    required = True
    verbose_name ='FOCUS_COMPANY_CODE'


@global_preferences_registry.register
class FocusUserName(StringPreference):
    section = thirdparty
    name = 'FOCUS_USERNAME'
    default = ''
    required = True
    verbose_name ='FOCUS_USERNAME'


@global_preferences_registry.register
class FocusPassword(StringPreference):
    section = thirdparty
    name = 'FOCUS_PASSWORD'
    default = ''
    required = True
    verbose_name ='FOCUS_PASSWORD'



@global_preferences_registry.register
class FocusLastSyncOn(StringPreference):
    section = thirdparty
    name = 'FOCUS_LAST_SYNC_ON'
    default = ''
    required = True
    verbose_name ='FOCUS_LAST_SYNC_ON'


@global_preferences_registry.register
class AmcuSyncOn(ChoicePreference):
    choices = [
                ('T', 'TRUE'),
                ('F', 'FALSE'),
            ]
    section = thirdparty
    name = 'AMCU_SYNC_ON'
    default = ''
    required = True
    verbose_name ='AMCU_SYNC_ON'


@global_preferences_registry.register
class AmcuBaseUrl(StringPreference):
    section = thirdparty
    name = 'AMCU_BASEURL'
    default = ''
    required = True
    verbose_name ='AMCU_BASEURL'


@global_preferences_registry.register
class AmcuUserName(StringPreference):
    section = thirdparty
    name = 'AMCU_USERNAME'
    default = ''
    required = True
    verbose_name ='AMCU_USERNAME'


@global_preferences_registry.register
class AmcuPassword(StringPreference):
    section = thirdparty
    name = 'AMCU_PASSWORD'
    default = ''
    required = True
    verbose_name ='AMCU_PASSWORD'



@global_preferences_registry.register
class AmcuApiKey(StringPreference):
    section = thirdparty
    name = 'AMCU_API_KEY'
    default = ''
    required = True
    verbose_name ='AMCU_API_KEY'


@global_preferences_registry.register
class AmcuLastSyncOn(StringPreference):
    section = thirdparty
    name = 'AMCU_LAST_SYNC_ON'
    default = ''
    required = True
    verbose_name ='AMCU_LAST_SYNC_ON'