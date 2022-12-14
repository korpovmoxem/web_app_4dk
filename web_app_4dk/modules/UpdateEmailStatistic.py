from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.ElementCallStatistic import update_element


# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)

month_string = {
        '01': 'Январь',
        '02': 'Февраль',
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '06': 'Июнь',
        '07': 'Июль',
        '08': 'Август',
        '09': 'Сентябрь',
        '10': 'Октябрь',
        '11': 'Ноябрь',
        '12': 'Декабрь'
    }


def update_company_statistic(company_id):
    update_element(company_id=company_id, outgoing_email=True)



def update_email_statistic(activity_info: dict):
    """
    Запускается из UpdateUserStatistics

    :param activity_info: данные о деле, полученные через crm.activity.get
    :return:
    """
    if activity_info['DIRECTION'] == '2':
        if activity_info['OWNER_TYPE_ID'] == '4':       # Компания
            update_company_statistic(activity_info['OWNER_ID'])

        elif activity_info['OWNER_TYPE_ID'] == '3':
            contact_id = activity_info['OWNER_ID']
            companies = b.get_all('crm.contact.company.items.get', {'id': contact_id})
            for company in companies:
                company_id = company['COMPANY_ID']
                update_company_statistic(company_id)

        elif activity_info['OWNER_TYPE_ID'] == '2':
            deal = b.get_all('crm.deal.get', {'id': activity_info['OWNER_ID']})
            company_id = deal['COMPANY_ID']
            update_company_statistic(company_id)

        elif activity_info['OWNER_TYPE_ID'] == '1':
            lead = b.get_all('crm.lead.get', {'id': activity_info['OWNER_ID']})
            company_id = lead['COMPANY_ID']
            update_company_statistic(company_id)

