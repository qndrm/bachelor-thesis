from django.shortcuts import get_object_or_404, render, redirect 
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import CreateView,DetailView
from django.views import View
from django.http import HttpResponse,JsonResponse,Http404
from .models import UserRequest,ProteinSequence,RequestStatistics
from .forms import UserRequestForm,SearchForm,EmailForm,UserRequestAPIForm
from .utils import user_input_to_file ,get_script
import csv
from .config import CHECK_TASK_TIMEOUT_MS 
from .tasks import send_email 
from rest_framework import views 
from rest_framework.response import Response
from .serializers import UserRequestSerializer
from django.utils import timezone
from django.db.models import  Sum
from django.utils.text import slugify


class HomeView(CreateView):
    def get(self,request,*args,**kwargs): 
        statistics = self.get_stats() # gets amount of total and monthly requests and proteinsequences
        context = {'form':UserRequestForm(),
                   'stats':statistics}
        return render(request,'home.html',context)
    
    def post(self,request,*args,**kwargs):

        form = UserRequestForm(request.POST,request.FILES)

        if form.is_valid():

            user_input = self.handle_user_input(form) # get userin_input as string

            if user_input:
                filepath , number_of_sequences = user_input_to_file(user_input) # create file from user_input

                if number_of_sequences < 1 : 
                    context = {
                    'form':UserRequestForm(),
                    'msg':'No valid input provided 1 '                    
                    }
                    return render(request,'home.html',context)
                file_hash = filepath.rsplit('/',1)[1] # filename is the hash
                if UserRequest.objects.filter(hash=file_hash).exists(): #check if user_request with this hash already exists
                    return  redirect('results',pk=file_hash)
                user_request = UserRequest.create_user_request_from_file(filepath,number_of_sequences)
                RequestStatistics.objects.create(number_of_sequences=user_request.number_of_sequences)
                return redirect('wait',pk=user_request.hash) 
            else:
                print(5)
                #if there is no userinput send a error message
                statistics = self.get_stats()
                context = {
                    'form':UserRequestForm(),
                    'stats':statistics,
                    'msg':'No input provided '                   
                    }
                return render(request,'home.html',context)
        else:
            #if form is not valid let user try again
            statistics = self.get_stats()
            context = {
                    'form':UserRequestForm(),
                    'stats':statistics,
                    'msg':'There was a problem please try again',                    
                    }
            return render(request,'home.html',context)
        
    def handle_user_input(self,form):
        file = form.cleaned_data.get('file') #get file from form
        user_input = form.cleaned_data.get('user_input') #get user_input from form
        if file :
            #if file is provided
            user_input_from_file = file.read().decode('utf-8')
            if user_input:
                #if user_input is also provided append file to user_input
                user_input = user_input + '\n' + user_input_from_file
            else:
                user_input = user_input_from_file
        # if there is no file just use user_input
        return user_input
    
    
    def get_stats(self):
        now = timezone.now()

        # Start of this month
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Requests
        requests_month = RequestStatistics.objects.filter(created_at__gte=start_month).count()
        requests_total = RequestStatistics.objects.all().count()

        # Sequences evaluated
        sequences_month = RequestStatistics.objects.filter(created_at__gte=start_month).aggregate(total=Sum('number_of_sequences'))['total'] or 0
        sequences_total = RequestStatistics.objects.aggregate(total=Sum('number_of_sequences'))['total'] or 0

        stats = {
            "requests": {
                "this_month": requests_month,
                "total": requests_total,
                "label": "Total requests"
            },
            "sequences_evaluated": {
                "this_month": sequences_month,
                "total": sequences_total,
                "label": "Total sequences evaluated"
            }
        }

        return stats


        
        
class UserGuide(View):
    def get(self,request,*args,**kwargs): 

        return render(request,'user-guide.html',{})

class DeleteView(View):
    model = UserRequest
    def get(self, request, *args, **kwargs):
        user_request_hash = kwargs.get('pk')
        user_request = get_object_or_404(UserRequest,hash=user_request_hash)
        user_request.delete()
        
        return redirect('home')


class WaitView(DetailView):
    model = UserRequest
    template_name = 'wait.html'
    context_object_name = 'user_request'
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['timeout'] = CHECK_TASK_TIMEOUT_MS # time for java script to check on the status of user request in ms
        context['form']= EmailForm()
        return context

    
    
    def post(self,request,*args,**kwargs):
        #post request to provide email to get notified when results are ready
        form = EmailForm(request.POST)
        if form.is_valid():
            user_request_hash = kwargs.get('pk')  
            user_request = get_object_or_404(UserRequest,hash=user_request_hash) #get user_request
            user_request.email = form.cleaned_data.get('email') 
            user_request.save() #add given email to user_request model
            total_sequences = user_request.number_of_sequences
            completed_sequences = len(user_request.proteinsequence_set.all())
            if total_sequences == 0:
                percentage = '0'
            else :
                percentage = str((completed_sequences / total_sequences)*100) # calculate progress
            send_email.delay(user_request_hash) #start celery task to send email when results are ready
            context = {'msg':'Email will be sent to : ' + user_request.email ,
                       'user_request': user_request,
                       'timeout': CHECK_TASK_TIMEOUT_MS ,
                       'form':EmailForm(), #send email form so that email can be changed if there was an typo
                       'progress':percentage}
            return render(request,'wait.html',context)
        

class StatusView(View):
    
    def get(self,request,*args,**kwargs):
        user_request_hash = kwargs.get('pk')   
        user_request = get_object_or_404(UserRequest,hash=user_request_hash) #get userrequest
        total_sequences = user_request.number_of_sequences
        completed_sequences = len(user_request.proteinsequence_set.all())
        percentage = str((completed_sequences / total_sequences)*100) # calculate progress
        return JsonResponse({'progress':percentage})




class ResultsView(DetailView):
    model = UserRequest
    template_name = 'results.html'
    context_object_name = 'user_requests'
    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if not pk:
            raise Http404("No user request found with this ID.")  
        try:
            return UserRequest.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404("No user request found with this ID.")
        
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sequences'] = self.object.proteinsequence_set.all
        return context
    

class Search(View):
    def get(self,request,*args,**kwargs):
        context = {'form':SearchForm()}
        return render(request,'search.html',context)
    
    def post(self,request,*args,**kwargs):
        hash = request.POST['hash']
        if hash == '': #if no hash is provided send error message
            context = {'form':SearchForm(), 'msg':'No request with this hash provided'}
            return render(request,'search.html',context)
        try:
            hash = hash.strip()
            get_object_or_404(UserRequest,hash=hash) # get user request
            return redirect('results',pk=hash)
        except Http404: # if there is no user request with this hash send error message
            context = {'form':SearchForm(), 'msg':'No request with this hash was found'}
            return render(request,'search.html',context)

    
class DownloadCsvView(View):
    def get(self,request,*args,**kwargs):
        response = HttpResponse(content_type='text/csv')
        
        writer = csv.writer(response)
        writer.writerow(['identifiers','sequence','score','thermophilic'])
        
        user_request_hash = kwargs.get('pk')
        user_request = get_object_or_404(UserRequest,hash=user_request_hash)
        
        for sequence in ProteinSequence.objects.filter(user_request=user_request).values_list('identifiers','sequence','score','thermophilic'):
            writer.writerow(sequence)
            
        response['Content-Disposition'] = f'attachment; filename={user_request_hash}_ProLaTherm.csv'
        
        
        return response

class DownlaodScriptView(View):
    def get(self, request, *args, **kwargs):
        script_content = get_script()
        
        response = HttpResponse(script_content, content_type='text/x-python')
        response['Content-Disposition'] = f'attachment; filename={"PLT-script.py"}'

        return response


class UserRequestAPIView(views.APIView):
    def post(self, request):
        form = UserRequestAPIForm(request.POST,request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get('file')
            email = form.cleaned_data.get('email')
            if file:
                user_input = file.read().decode('utf-8')
            if user_input:
                filepath, number_of_sequences = user_input_to_file(user_input)
                file_hash = filepath.rsplit('/', 1)[1]
                if number_of_sequences < 1:
                    return Response({"error": "The file is has 0 valid sequences."}, status=400)
                if UserRequest.objects.filter(hash=file_hash).exists():
                    user_request = UserRequest.objects.get(hash=file_hash)
                else:
                    user_request = UserRequest.create_user_request_from_file(filepath, number_of_sequences)
                    if email:
                        user_request.email = email
                        user_request.save()
                        send_email.delay(file_hash)
            else:
                return Response({"error": "The file is empty."}, status=400)

            return Response({
                    'message': f"You will be able to find your results at http://127.0.0.1:8000/results/{user_request.hash}",
                    'user_request': UserRequestSerializer(user_request).data,
                })
        return Response(form.errors, status=400)
    
    
class StatusAPIView(views.APIView):
    def get(self,request,*args,**kwargs):
        user_request_hash = kwargs.get('pk')   
        user_request = get_object_or_404(UserRequest,hash=user_request_hash) # get user request
        total_sequences = user_request.number_of_sequences
        completed_sequences = len(user_request.proteinsequence_set.all())
        percentage = str((completed_sequences / total_sequences)*100) # calculate percentage
        if completed_sequences == total_sequences:
            return JsonResponse({'status': 'ready', 'progress': percentage})#,'p_time':user_request.process_time})
        else:
            return JsonResponse({'status': 'processing', 'progress': percentage})
        
class DownloadCsvAPIView(views.APIView):
    def get(self, request, *args, **kwargs):
        
        user_request_hash = kwargs.get('pk')   
        user_request = get_object_or_404(UserRequest,hash=user_request_hash) # get user request

        response = HttpResponse(content_type='text/csv')
        writer = csv.writer(response)
        writer.writerow(['identifiers', 'sequence', 'score', 'thermophilic']) # write header row
        
        for sequence in ProteinSequence.objects.filter(user_request=user_request).values_list('identifiers', 'sequence', 'score', 'thermophilic'):
            writer.writerow(sequence)
            

        response['Content-Disposition'] = f'attachment; filename={user_request_hash}_ProLaTherm.csv'

        return response