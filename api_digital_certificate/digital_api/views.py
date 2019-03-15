from django.http import JsonResponse
from django.views import View
import requests
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.conf import settings


class DigitalCertificateView(View):
    def sign_token(self, key):
        get_signature = requests.post(
            settings.SIGNATURE_URL,
            data="[{}]".format(key),
            verify=False
        ).json()
        data = dict(
            signature=list(get_signature['assinaturas'].values())[0],
            certChain=get_signature['certchain'],
            certChainStringLog='',
            status='ok'
        )

        return data

    @method_decorator(login_required)
    def get(self, request):
        if request.GET.get('key'):
            response = self.sign_token(request.GET.get('key'))
            response = JsonResponse(data=response)

            return response

        return JsonResponse({'status': 'fail'})
