from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os

@csrf_exempt
@login_required
def upload_chat_image_api(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        # Save to media/chat_images/
        save_path = os.path.join('chat_images', image.name)
        path = default_storage.save(save_path, ContentFile(image.read()))
        image_url = settings.MEDIA_URL + path
        return JsonResponse({'success': True, 'url': image_url})
    return HttpResponseBadRequest('Invalid request') 