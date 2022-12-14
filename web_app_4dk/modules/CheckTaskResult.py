from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt
webhook = authentication('Bitrix')
b = Bitrix(webhook)



def check_task_result(dct):
    if 'group_id' in dct:
        if dct['group_id'] == '89':
            stage_comments = {
                '1269': 'Вы взяли задачу в работу. Позвоните пользователю, уточните, использует ли он в работе сервис, и получена ли подпись ФНС.',
                '1275': 'Кратко объясните пользователю последствия, зафиксируйте дату следующего контакта в поле крайнего срока или в комментарии',
                '1271': 'Требуется создать заявление на изменение, используя подпись ФНС, дождитесь обработки заявления (сообщите в офис о создании заявления) и завершите задачу',
                '1273': 'Пользователь не в курсе, получена или нет подпись. Зафиксируйте дату следующего контакта в поле крайнего срока или в комментарии',
            }
            b.call('task.commentitem.add', [dct['id'], {'POST_MESSAGE': stage_comments[dct['stage_id']], 'AUTHOR_ID': '173'}],
                   raw=True)
    else:
        flag = False
        id = dct['id']
        task = b.get_all('task.commentitem.getlist', {'ID': id})
        for comment in task:
            if '[USER=333]' in comment['POST_MESSAGE']:
                flag = True
        if flag is False:
            b.call('tasks.task.update', {'taskId': id, 'fields': {'STAGE_ID': '1117'}})



