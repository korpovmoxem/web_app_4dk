from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def complete_call_activity(req):
    activity_id = req['data[FIELDS][ID]']
    print(activity_id)