import typing
import traceback
import urllib.parse #URL encode
import mitmproxy.addonmanager
import mitmproxy.connections
import mitmproxy.http
import mitmproxy.log
import mitmproxy.tcp
import mitmproxy.websocket
import mitmproxy.proxy.protocol

# The next is official docs: https://docs.mitmproxy.org/stable/addons-events/
class Events:
    features = {'webdriver',
        '__driver_evaluate',
        '__webdriver_evaluate',
        '__selenium_evaluate',
        '__fxdriver_evaluate',
        '__driver_unwrapped',
        '__webdriver_unwrapped',
        '__selenium_unwrapped',
        '__fxdriver_unwrapped',
        '_Selenium_IDE_Recorder',
        '_selenium',
        'calledSelenium',
        '_WEBDRIVER_ELEM_CACHE',
        'ChromeDriverw',
        'driver-evaluate',
        'webdriver-evaluate',
        'selenium-evaluate',
        'webdriverCommand',
        'webdriver-evaluate-response',
        '__webdriverFunc',
        '__webdriver_script_fn',
        '__$webdriverAsyncExecutor',
        '__lastWatirAlert',
        '__lastWatirConfirm',
        '__lastWatirPrompt',
        '$chrome_asyncScriptInfo',
        '$cdc_asdjflasutopfhvcZLmcfl_'
        '_phantom',
        'callPhantom',
        'callSelenium',
        'selenium',
        'document_webdriver',
        'document_driver'
    }
    # HTTP lifecycle
    def http_connect(self, flow: mitmproxy.http.HTTPFlow):
        """
            An HTTP CONNECT request was received. Setting a non 2xx response on
            the flow will return the response to the client abort the
            connection. CONNECT requests and responses do not generate the usual
            HTTP handler events. CONNECT requests are only valid in regular and
            upstream proxy modes.
        """

    def requestheaders(self, flow: mitmproxy.http.HTTPFlow):
        """
            HTTP request headers were successfully read. At this point, the body
            is empty.
        """

    def request(self, flow: mitmproxy.http.HTTPFlow):
        """
            The full HTTP request has been read.
        """
        # flow.request.replace(urllib.parse.quote('苟全'), urllib.parse.quote('和谐'))
        # if flow.request.host == 'www.baidu.com':
        #     flow.request.host = 'www.so.com'

    def responseheaders(self, flow: mitmproxy.http.HTTPFlow):
        """
            HTTP response headers were successfully read. At this point, the body
            is empty.
        """

    def response(self, flow: mitmproxy.http.HTTPFlow):
        """
            The full HTTP response has been read.
        """
        # 逐一替换特征词
        for feature in self.features:
            if flow.response.content.__contains__(feature.encode('UTF-8')):
                print('Contain:', feature, end='\n------------------------\n')
                flow.response.content = flow.response.content.replace(feature.encode('UTF-8'),
                    'anti_'.encode('UTF-8')+feature.encode('UTF-8'))
        # TODO:读取mitm策略并注入script
        flow.response.content = flow.response.content.replace('<script>'.encode('UTF-8'),
            '''
            <script>
                Object.defineProperty(navigator, 'webdriver', {get: () => false,});
                window.chrome.runtime = {};
                Object.defineProperty(navigator, "languages", {get: function() {return ["en-US", "en", "es"];}});\n
            </script>
            <script>
            '''.encode('UTF-8'), 1)
        # 获取商品url

        # 获取商品标题

        # 商品名称

        # 查询满减券
        # 查找第一个script位置
        # script_pos = print('\n-------------------\nAt pos:',
        #     flow.response.content.find("&lt;script&gt;".encode('UTF-8')))

    def error(self, flow: mitmproxy.http.HTTPFlow):
        """
            An HTTP error has occurred, e.g. invalid server responses, or
            interrupted connections. This is distinct from a valid server HTTP
            error response, which is simply a response with an HTTP error code.
        """

    # TCP lifecycle
    def tcp_start(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP connection has started.
        """

    def tcp_message(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP connection has received a message. The most recent message
            will be flow.messages[-1]. The message is user-modifiable.
        """

    def tcp_error(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP error has occurred.
        """

    def tcp_end(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP connection has ended.
        """

    # Websocket lifecycle
    def websocket_handshake(self, flow: mitmproxy.http.HTTPFlow):
        """
            Called when a client wants to establish a WebSocket connection. The
            WebSocket-specific headers can be manipulated to alter the
            handshake. The flow object is guaranteed to have a non-None request
            attribute.
        """

    def websocket_start(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            A websocket connection has commenced.
        """

    def websocket_message(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            Called when a WebSocket message is received from the client or
            server. The most recent message will be flow.messages[-1]. The
            message is user-modifiable. Currently there are two types of
            messages, corresponding to the BINARY and TEXT frame types.
        """

    def websocket_error(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            A websocket connection has had an error.
        """

    def websocket_end(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            A websocket connection has ended.
        """

    # Network lifecycle
    def clientconnect(self, layer: mitmproxy.proxy.protocol.Layer):
        """
            A client has connected to mitmproxy. Note that a connection can
            correspond to multiple HTTP requests.
        """

    def clientdisconnect(self, layer: mitmproxy.proxy.protocol.Layer):
        """
            A client has disconnected from mitmproxy.
        """

    def serverconnect(self, conn: mitmproxy.connections.ServerConnection):
        """
            Mitmproxy has connected to a server. Note that a connection can
            correspond to multiple requests.
        """

    def serverdisconnect(self, conn: mitmproxy.connections.ServerConnection):
        """
            Mitmproxy has disconnected from a server.
        """

    def next_layer(self, layer: mitmproxy.proxy.protocol.Layer):
        """
            Network layers are being switched. You may change which layer will
            be used by returning a new layer object from this event.
        """

    # General lifecycle
    def configure(self, updated: typing.Set[str]):
        """
            Called when configuration changes. The updated argument is a
            set-like object containing the keys of all changed options. This
            event is called during startup with all options in the updated set.
        """

    def done(self):
        """
            Called when the addon shuts down, either by being removed from
            the mitmproxy instance, or when mitmproxy itself shuts down. On
            shutdown, this event is called after the event loop is
            terminated, guaranteeing that it will be the final event an addon
            sees. Note that log handlers are shut down at this point, so
            calls to log functions will produce no output.
        """

    def load(self, entry: mitmproxy.addonmanager.Loader):
        """
            Called when an addon is first loaded. This event receives a Loader
            object, which contains methods for adding options and commands. This
            method is where the addon configures itself.
        """

    def log(self, entry: mitmproxy.log.LogEntry):
        """
            Called whenever a new log entry is created through the mitmproxy
            context. Be careful not to log from this event, which will cause an
            infinite loop!
        """

    def running(self):
        """
            Called when the proxy is completely up and running. At this point,
            you can expect the proxy to be bound to a port, and all addons to be
            loaded.
        """

    def update(self, flows: typing.Sequence[mitmproxy.flow.Flow]):
        """
            Update is called when one or more flow objects have been modified,
            usually from a different addon.
        """


addons = [Events()]

