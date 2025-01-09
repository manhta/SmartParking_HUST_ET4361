from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.dispatch import receiver
from django.db.models.signals import post_save

import requests
import json

from myapp.models import Card
from myapp.forms import CardAddForm

from decimal import Decimal

esp32_url = "http://172.20.10.3"  # URL của ESP32

# Create your views here.
def homeview(request):
    cards = Card.objects.all().order_by('cardName')
    count = cards.count()

    context = {
        'cards': cards,
        'count': count,
    }

    return render(request, 'homeview.html', context)

@receiver(post_save, sender=Card)
def sendNewData(sender, instance, created, **kwargs):
    if created:  # Chỉ gửi nếu object mới được tạo
        data = {
            'cardName': instance.cardName,
            'cardBalance': str(instance.cardBalance)
        }
        try:
            esp32_receive_data_url = esp32_url+'/add_data'  # URL của ESP32
            response = requests.post(esp32_receive_data_url, data=data)
            response.raise_for_status()
            print(f"Response code: {response.status_code}")
            print(f"Response data: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to ESP32: {e}")

def addCard(request):
    if request.method == 'POST':
        form = CardAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm thẻ thành công!')
            return redirect('homeview')  # Redirect về trang chủ sau khi thêm thành công
    else:
        form = CardAddForm()

    return render(request, 'add_card.html', {'form': form})

def recharge(request, id):
    card = Card.objects.get(id=id)

    if request.method == 'POST':
        added_balance = request.POST.get('added_balance')
        if added_balance:
            try:
                # Cộng thêm số dư
                added_balance = Decimal(added_balance)
                card.cardBalance += added_balance
                card.save()

                # Gửi thông tin nạp tiền đến ESP32
                esp32_update_data_url = esp32_url+"/update_data" 

                data = {
                    'cardName': card.cardName,
                    'newCardBalance': str(card.cardBalance)
                }

                response = requests.post(esp32_update_data_url, data=data)
                response.raise_for_status()
                print(f"Response code: {response.status_code}")
                print(f"Response data: {response.text}")

                # Thông báo thành công
                messages.success(request, 'Nạp tiền thành công!')
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Không thể gửi thông tin nạp tiền đến ESP32: {e}")
            except ValueError:
                messages.error(request, "Giá trị nạp tiền không hợp lệ!")

            return redirect('homeview')

    return render(request, 'recharge.html', {'card': card})

def deleteCard(request, id):
    card = Card.objects.get(id=id)

    if request.method == 'POST':
        # Gửi thông báo xóa đến ESP32
        try:
            esp32_delete_data_url = esp32_url+"/delete_data"  # URL của ESP32
            data = {'deletedCardName': card.cardName}  # Gửi tên thẻ hoặc thông tin liên quan
            response = requests.post(esp32_delete_data_url, data=data)  # Gửi yêu cầu HTTP POST
            response.raise_for_status()  # Kiểm tra trạng thái phản hồi
            print(f"Response code: {response.status_code}")
            print(f"Response data: {response.text}")
                
            # Xóa thẻ sau khi thông báo xóa thành công
            card.delete()
            messages.success(request, 'Sản phẩm đã được xóa thành công!')

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Không thể thông báo xóa thẻ đến ESP32: {e}")

        return redirect('homeview')  # Redirect về homepage sau khi xóa

    return render(request, 'delete_card.html', {'card': card})

def fetchData(request):
    cards = Card.objects.all()
    data = [
        {
            'cardName': card.cardName,
            'cardBalance': card.cardBalance
        }
        for card in cards
    ]
    
    return JsonResponse(data, safe=False)  # safe=False allows returning a list instead of a dictionarypass


@csrf_exempt  # Exempt this view from CSRF checks (use caution in production).
def updateBalanceFromESP(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) 
            card = Card.objects.get(cardName = data.get('cardName'))
            print(card.cardBalance)
            card.cardBalance = Decimal(data.get('cardNewBalance'))
            print('card new balance: ', data.get('cardNewBalance'))
            card.save()

            return JsonResponse({"status": "success", "message": "Data received successfully."})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON data."}, status=400)
    return JsonResponse({"status": "error", "message": "Only POST method is allowed."}, status=405)


