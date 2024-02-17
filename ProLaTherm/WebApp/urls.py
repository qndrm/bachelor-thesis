from django.urls import path
from .views import *

urlpatterns = [
    path('',HomeView.as_view(),name='home'),# Home view
    path('results/<str:pk>',ResultsView.as_view(),name='results'), # where results are shown
    path('wait/<str:pk>',WaitView.as_view(),name='wait'), # waiting screen
    path('csv/<str:pk>',DownloadCsvView.as_view(),name='download-csv'),# to download results as csv
    path('status/<str:pk>/', StatusView.as_view(), name='status'),# used in the wait view to check if results are ready
    path('search/',Search.as_view(),name='search'),# search bar to find request based on hash
    path('delete/<str:pk>',DeleteView.as_view(),name='delete'),
    path('user-guide/',UserGuide.as_view(),name='user-guide'),
    path('script/', DownlaodScriptView.as_view(),name="downlaod-script"),
    path('api/user-request/', UserRequestAPIView.as_view(), name='user-request-api'),# api endpoint to evaluate data 
    path('api/status/<str:pk>/', StatusAPIView.as_view(), name='status-api'), # same as the other status just as an api enpoint
    path('api/csv/<str:pk>/', DownloadCsvAPIView.as_view(), name='csv-download-api'),# same as the other csv just as an api endpoint
]

