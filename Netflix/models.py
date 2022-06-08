from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.validators import FileExtensionValidator
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SKEY



    


# Create your models here.

class Customer(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
    date_paid = models.DateField(null=True,default=None)

    def __str__(self):
        return self.user.email

Category = (
    ('TRENDING NOW','Trending Now'),
    ('TV SHOWS','TV Shows'),
    ('TOP PICKS','Top Picks'),
    ('MUST WATCH','Must Watch Shows'),
    ('AGAIN','Watch It Again'),
)



class Movies(models.Model):
    title = models.CharField(max_length=50)
    desc = models.CharField(max_length=200)
    duration = models.DurationField(default=timedelta(minutes=0))
    poster = models.ImageField(upload_to='images')
    category = models.CharField(max_length=25,choices=Category, default='MUST WATCH')
    price = models.IntegerField(default=1)
    trailer = models.URLField()
    video_file = models.FileField(upload_to='videos',null=True,
    validators=[FileExtensionValidator(allowed_extensions=['MOV','avi','mp4','webm','mkv'])])
    stripe_id = models.CharField(max_length=50,null=True,blank=True)

    def create_stripe(self,prod,price):
        pr = stripe.Product.create(name=prod)
        p = stripe.Price.create(
        unit_amount=price*100,
        currency="inr",
        product=pr.id,
        )
        return p.id 


    def save(self,*args,**kwargs):
        if not self.stripe_id:
            self.stripe_id = self.create_stripe(self.title,self.price)  
        super(Movies,self).save(*args,**kwargs) 


    def __str__(self):
        return self.title


class Orders(models.Model):
    user = models.ForeignKey(Customer,on_delete=models.CASCADE)
    movie = models.ForeignKey(Movies,on_delete=models.CASCADE)
    watch_cnt = models.IntegerField(default=0)
