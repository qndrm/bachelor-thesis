from django.db import models
from .config import SEQUENCES_PER_TASK,SPLIT_TASKS
import os ,re ,time

class RequestStatistics(models.Model):
    number_of_sequences = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
class UserRequest(models.Model):
    hash = models.CharField(max_length=64,primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    number_of_sequences = models.IntegerField(default=0)
    email = models.EmailField(null=True,blank=True)
    #process_time = models.BigIntegerField(default=0)
    
    @staticmethod
    def create_user_request_from_file(filepath,number_of_sequences):
        file_hash = filepath.rsplit('/',1)[1] #get hash from filepath
        if UserRequest.objects.filter(hash=file_hash).exists(): #check if userrequest already exists
            user_request =UserRequest.objects.get(hash=file_hash)
            return user_request
        user_request = UserRequest.objects.create(hash=file_hash) # create user request
        user_request.number_of_sequences = number_of_sequences
        user_request.save()
        ProteinSequence.create_protein_sequence_from_file(user_request.hash,filepath)# create protein sequences 
        return user_request
    

class ProteinSequence(models.Model): #neue namen ?
    user_request = models.ForeignKey(UserRequest,on_delete=models.CASCADE) #user_request as foreign key if user_request get's deleted also delete protein sequence
    identifiers = models.CharField(max_length=255)
    sequence = models.TextField()
    score = models.FloatField()
    thermophilic = models.BooleanField()
    
    @staticmethod
    def create_protein_sequence_from_file(user_request_hash,filepath):
        from .tasks import async_evaluate
        with open(filepath,'r') as file:
            f = file.read()
        
        if f.count('>') <= SEQUENCES_PER_TASK or not SPLIT_TASKS: # if there are less than SEQUENCES_PER_TASK sequences just run evalaution once

            eval = async_evaluate.delay(user_request_hash,filepath)



            return eval
        else:
            #if we split them up get sequences in a list
            to_evaluate = re.split("(?=>)", f)
            list_chunked = [to_evaluate[i:i + SEQUENCES_PER_TASK ] for i in range(0, len(to_evaluate), SEQUENCES_PER_TASK)]
            #list of lists of sequences with SEQUENCES_PER_TASK length
            for i , temp in enumerate(list_chunked):
                temp_filepath = os.path.join(os.getcwd()+"/WebApp/evalRequests/",user_request_hash+'_'+str(i))
                with open(temp_filepath,"w") as file: # create file with hash as name in write mode
                    file.write(''.join(temp))
                async_evaluate.delay(user_request_hash,temp_filepath)
            os.remove(filepath)