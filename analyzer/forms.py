from django import forms
from .models import ProductImage

class ProductImageForm(forms.ModelForm):
    """商品圖片上傳表單"""
    
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'multiple': False
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].label = '選擇商品圖片'
        self.fields['image'].help_text = '支援 JPG、PNG、GIF 等圖片格式'