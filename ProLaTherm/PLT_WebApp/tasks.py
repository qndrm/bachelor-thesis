from celery import shared_task 



@shared_task(queue='delete')
def delete_old_user_requests(string):
        print(string)