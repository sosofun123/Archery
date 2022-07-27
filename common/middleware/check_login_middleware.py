# -*- coding: UTF-8 -*-
import re
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

IGNORE_URL = [
    '/archery/login/',
    '/archery/authenticate/',
    '/archery/signup/',
    '/archery/sislogin/',
    '/archery/api/info'
]

IGNORE_URL_RE = r'/admin/\w*'


class CheckLoginMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        """
        该函数在每个函数之前检查是否登录，若未登录，则重定向到/login/
        """
        if not request.user.is_authenticated:
            if settings.ENABLE_OPENID_CONNECT:
                #if
                return HttpResponseRedirect(settings.AUTH_URL)
            else:
                # 以下是不用跳转到login页面的url白名单
                if request.path not in IGNORE_URL and re.match(IGNORE_URL_RE, request.path) is None:
                    return HttpResponseRedirect('/archery/login/')
