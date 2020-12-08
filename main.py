import logging

import requests
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from validator_collection import checkers

logger = logging.getLogger(__name__)


class ShortIT(Extension):

    def __init__(self):
        super(ShortIT, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

    def short_url(self, url: str, service: str):
        if checkers.is_url(url):
            return self.short(url, service)
        else:
            return self.url_error()

    def short(self, url: str, service: str):
        if service == "tly":
            tly_api_key = self.preferences.get("shortit_tly_apikey")
            if tly_api_key != "":
                return self.short_with_tly(tly_api_key, url)
            else:
                return self.apikey_error("Tly")
        elif service == "bitly":
            bitly_api_key = self.preferences.get("shortit_bitly_apikey")
            if bitly_api_key != "":
                return self.short_with_bitly(bitly_api_key, url)
            else:
                return self.apikey_error("Bitly")
        else:
            return self.unknownservice_error()

    def short_with_tly(self, api_key, url):
        logger.debug("Short with Tly")
        request_params = {
            'api_token': api_key,
            'long_url': url
        }
        request = requests.post("https://t.ly/api/v1/link/shorten", params=request_params)

        return [
            ExtensionResultItem(
                icon='images/tly.png',
                name=request.json()["short_url"],
                description='Made with Tly',
                on_enter=CopyToClipboardAction(request.json()["short_url"])
            )
        ]

    def short_with_bitly(self, api_key, url):
        logger.debug("Short with Bitly")
        data = "{\"long_url\":\"" + url + "\"}"
        headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
        request = requests.post("https://api-ssl.bitly.com/v4/shorten", headers=headers, data=data)

        return [
            ExtensionResultItem(
                icon='images/bitly.png',
                name=request.json()["link"],
                description='Made with Bitly',
                on_enter=CopyToClipboardAction(request.json()["link"])
            )
        ]

    def url_error(self):
        return self.simple_error_message("Something went wrong...", "Incorrent URL format.")
    
    def apikey_error(self, service: str):
        return self.simple_error_message("Empty API key", f"No API key for {service}. Please, check preferences.")

    def emptyurl_error(self):
        return self.simple_error_message("Now write the URL to short", "For example: https://my-awesome.web.com")

    def simple_error_message(self, title: str, message: str):
        return [
            ExtensionResultItem(
                icon='images/icon.png',
                name=title,
                description=message
            )
        ]

    def emptyservice_error(self):
        return self.service_error("Choose the short service")

    def unknownservice_error(self):
        return self.service_error("Unknown service")

    def service_error(self, title: str):
        keyword = self.preferences.get("shortit_keyword")
        return [
            ExtensionResultItem(
                icon='images/icon.png',
                name=title,
                description=f"Check available service typing {keyword} ? or press enter",
                on_enter=SetUserQueryAction(f"{keyword} ?")
            )
        ]

    def return_help(self):
        keyword = self.preferences.get("shortit_keyword")
        return [
            ExtensionResultItem(
                icon='images/tly.png',
                name="tly",
                description="Short using t.ly",
                on_enter=SetUserQueryAction(f"{keyword} tly ")
            ),
            ExtensionResultItem(
                icon='images/bitly.png',
                name="bitly",
                description="Short using bitly",
                on_enter=SetUserQueryAction(f"{keyword} bitly ")
            )
        ]


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []

        # Split command and options
        argument: str = event.get_argument() or ""
        if argument != "":
            service, *options = argument.split()

            if service == "?":
                return RenderResultListAction(extension.return_help())
            elif len(options) > 0:
                return RenderResultListAction(extension.short_url(options[0], service))
            else:
                return RenderResultListAction(extension.emptyurl_error())
        else:
            return RenderResultListAction(extension.emptyservice_error())


if __name__ == '__main__':
    ShortIT().run()
