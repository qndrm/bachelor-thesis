from celery import shared_task 
from .utils import evaluate , evaluate_mock
import os,time
from .config import HOST_EMAIL, RESULTS_URL , MOCK
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from .models import ProteinSequence, UserRequest
from django.utils import timezone
from datetime import timedelta

@shared_task(queue='eval')
def async_evaluate(user_request_hash,filepath):
    if MOCK:
        results = evaluate_mock(filepath) # start mock evaluation
    else:
        results = evaluate(filepath) # start evaluation
    user_request = UserRequest.objects.get(hash=user_request_hash) # get user request
    user_request.save()
    for index, row in results.iterrows():
        ids = row['IDs']
        aa_seq = row['aa-seq']
        prediction_binary = row['prediction_binary']
        score = row['score']
        #create protein sequences
        protein_sequence = ProteinSequence.objects.create(user_request=user_request,identifiers=ids,sequence=aa_seq, score=score, thermophilic=prediction_binary)
        protein_sequence.save()
    os.remove(filepath) # remove file when done
    
@shared_task(queue='email')
def send_email(user_request_hash):
    user_request = get_object_or_404(UserRequest,hash=user_request_hash) # get user reqeust
    total_sequences = user_request.number_of_sequences
    completed_sequences = len(user_request.proteinsequence_set.all())
    percentage = (completed_sequences / total_sequences) # calculate percentage
    email = user_request.email
    #wait until evaluation is done
    while percentage < 1.0: 
        time.sleep(5)
        total_sequences = user_request.number_of_sequences
        completed_sequences = len(user_request.proteinsequence_set.all())
        percentage = (completed_sequences / total_sequences)
    #update user_request in case the email was changed
    user_request.refresh_from_db()
    #print(f"sending email to {user_request.email}")
    if email == user_request.email: # check if email has been changed
        send_mail(
                    'ProLaTherm Results',
                    f'Your ProLaTherm Results are here :{RESULTS_URL}{user_request_hash}', #provide link to results in email
                    HOST_EMAIL,
                    [user_request.email],
                    fail_silently=False,)
    # if email has been changed don't send an email
        
@shared_task(queue='delete')
def delete_old_user_requests():
    #delete user request if it's older than 3 days
        time_threshold = timezone.now() - timedelta(days=30)
        UserRequest.objects.filter(created_at__lt=time_threshold).delete()