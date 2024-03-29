from fast_bitrix24 import Bitrix

from authentication import authentication


b = Bitrix(authentication('Bitrix'))

task_description = f'Коллеги, вам поставлена задача в рамках отработки на практике полученных теоретических знаний. Есть ряд клиентов по которым надо сделать результативный звонок контактному лицу.\n\nЗадачи, которые нужно выполнить.\n\n1. Провести анализ текущего состояния клиента, выбрать инфоповод, с которым вы заходите в клиента. Зафиксировать в комментарии к задаче инфоповоды с которым вы собираетесь заходить в клиента.\n\n2. Предлагаю инфоповоды: Повышение цен на ПП 1С с 01.04.23 (Обратите внимание, что особенно актуально для клиентов не на Фреше). Спарк Риски и 1С: Кабинет сотрудника (проверить есть ли у нас действующий договор на эти сервисы), Снятие с поддержки УТ 10 с 2024 года (спросить у клиента, на какой редакции работает клиент). Либо предложите свой вариант. План действий (выбранные инфоповоды зафиксировать в комментариях).\n\n3. Познакомиться с клиентом и актуализировать контактную информацию, наличие редакции УТ 10, проверить текущую сферу деятельности. Результат зафиксировать в комментарии к задаче.\n\n4. Озвучить предложение и выявить интерес. При выявлении интереса – договориться о следующие контакте. При отсутствии интереса – указать причину.\n\nДля фиксации действий и результата работы создана простая воронка:\n\n1. Новые – тут находятся задачи, которые нужно выполнить.\n\n2. Выполнение – клиент взят в работу, вы собираетесь клиенту звонить сегодня, до клиента не дозвонились, клиент попросил позвонить похоже и т.п.\n\n3. Есть интерес – клиент проявил интерес, озвучил проблему, есть договоренность с клиентом о КП/счете/встрече/следующем контакте. Всю историю переговоров отображайте в комментариях.\n\n4. Нет интереса – фиксируем причину отказа. Постарайтесь докопаться до истинной причины – клиенту не нужно – это не причина. Это мы не смогли донести ценность до клиента.\n\n5. Продажа – клиенту выставлен счет.'

deals_info = b.get_all('crm.deal.list', {
    'filter': {
        'UF_CRM_1657878818384': '859',
        'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6'],
        'ASSIGNED_BY_ID': ['133', '19', '153', '213'],
    }
})
used_companies = []
count = 0
for deal in deals_info:
    responsible = '405'
    if count % 2 == 0:
        responsible = '403'
    count += 1
    if deal['COMPANY_ID'] not in used_companies:
        b.call('tasks.task.add', {
            'fields': {
                'TITLE': 'Проработка',
                'GROUP_ID': '95',
                'UF_CRM_TASK': [f'CO_{deal["COMPANY_ID"]}'],
                'CREATED_BY': '173',
                'DEADLINE': '2023-01-25 19:00',
                'RESPONSIBLE_ID': responsible,
                'AUDITORS': ['391'],
                'DESCRIPTION': task_description
            }
        })
    used_companies.append(deal['COMPANY_ID'])
