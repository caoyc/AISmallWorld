"""telnetlib 兼容垫片（Python 3.12+ 适用）。

PEP 594 在 Python 3.12 移除了标准库 telnetlib，但本项目的部署脚本
scripts/build_world.py、scripts/create_player.py 仍依赖它走 telnet(4000)
连接 Evennia 执行 @py。这里实现脚本实际用到的最小子集：

    Telnet(host, port, timeout) / read_very_eager() / write(data) / close()

经实测（Evennia 6.1.0 / portal telnet 4000）确认的协商策略：

1. 行结束必须用 CRLF。脚本里写死的是 '\\n'，所以 write 自动把
   裸 '\\n' 归一化为 '\\r\\n'，否则 Evennia 不认输入行。
2. server 的 IAC WILL x 默认接受（回 DO x）——不回应则 Evennia
   不会下发欢迎文本与后续输出；但压缩选项 85/86（MCCP/COMPRESS2）
   必须 DONT，否则之后所有数据被 zlib 压缩，脚本无法识别。
3. server 的 IAC DO x 回 WONT x（客户端不启用这些选项）。
4. SB...SE 子协商吞掉；IAC IAC 还原为字面 0xFF。

如此 read_very_eager 返回纯文本，脚本对 'ALL OK' / '#10' / 'NOT FOUND'
等子串判断不受污染。
"""
import socket

# telnet 协议字节常量
_IAC = 255      # Interpret As Command
_DONT = 254
_DO = 253
_WONT = 252
_WILL = 251
_SB = 250       # Subnegotiation Begin
_SE = 240       # Subnegotiation End

# 压缩相关选项：必须拒绝，否则后续字节流被 zlib 压缩
_COMPRESS_OPTS = (85, 86)  # MCCP / COMPRESS2


class Telnet:
    def __init__(self, host=None, port=0, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.sock = None
        if host is not None:
            self.open(host, port, timeout)

    def open(self, host, port=0, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.sock = socket.create_connection((host, port), timeout)
        # 非阻塞：read_very_eager 语义是“读当前缓冲所有可得数据，无则立即返回 b''”
        self.sock.setblocking(False)

    def write(self, buffer):
        # telnet 行结束要求 CRLF：先归一再转换，避免 \r\n 被重复转成 \r\r\n
        buffer = buffer.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        self.sock.sendall(buffer)

    def _recv_all_available(self):
        chunks = []
        while True:
            try:
                data = self.sock.recv(4096)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                break
            if not data:
                break  # 连接关闭
            chunks.append(data)
        return b"".join(chunks)

    def read_very_eager(self):
        data = self._recv_all_available()
        if not data:
            return b""

        out = bytearray()
        replies = bytearray()
        i = 0
        n = len(data)
        while i < n:
            b = data[i]
            if b != _IAC:
                out.append(b)
                i += 1
                continue

            # 命中 IAC
            if i + 1 >= n:
                break  # 不完整的协商，留给下次
            opt = data[i + 1]

            if opt == _WILL and i + 2 < n:
                what = data[i + 2]
                resp = _DONT if what in _COMPRESS_OPTS else _DO
                replies += bytes([_IAC, resp, what])
                i += 3
            elif opt == _DO and i + 2 < n:
                replies += bytes([_IAC, _WONT, data[i + 2]])
                i += 3
            elif opt in (_DONT, _WONT) and i + 2 < n:
                i += 3  # 无需回应
            elif opt == _SB:
                # 子协商：跳到 IAC SE
                j = data.find(bytes([_IAC, _SE]), i)
                i = (j + 2) if j != -1 else n
            elif opt == _IAC:
                out.append(_IAC)  # IAC IAC -> 字面 0xFF
                i += 2
            else:
                i += 2  # 其它两字节命令（如 GA），吞掉
        if replies:
            try:
                self.sock.sendall(bytes(replies))
            except OSError:
                pass
        return bytes(out)

    def close(self):
        try:
            if self.sock is not None:
                self.sock.close()
        except OSError:
            pass
