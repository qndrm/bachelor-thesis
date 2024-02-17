from django import forms




class UserRequestForm(forms.Form):
    user_input = forms.CharField(required=False, widget=forms.Textarea(attrs={'class':'form-control',}))
    file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class':'form-control',}))





class SearchForm(forms.Form):
    hash = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control',}))
    
class EmailForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email'}),
    )

class UserRequestAPIForm(forms.Form):
    file = forms.FileField()
    email = forms.EmailField(required=False)
