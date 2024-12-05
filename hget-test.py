#!/usr/bin/env python
# encoding: utf-8


import os
import unittest
import hget

TEMPFILE = 'test.tmp'


class FakeSocket(object):

    def __init__(self, data=()):
        self.sent = list(data)

    def sent_data(self):
        return (''.join(self.sent)).encode()

    def recv(self, count):
        result = ''.join(self.sent[:count])
        del self.sent[:count]
        return result.encode()

    def send(self, data):
        data = data.decode()
        self.sent += list(data)


class HgetTest(unittest.TestCase):

    def test_send_request(self):
        fake = FakeSocket('')
        hget.send_request(fake, 'abcde')
        self.assertEqual(fake.sent_data(), b'GET abcde HTTP/1.0\r\n\r\n')

    def test_read_line(self):
        fake = FakeSocket('text line\r\nother line\r\n')
        line = hget.read_line(fake)
        self.assertEqual(line, b'text line\r\n')
        line = hget.read_line(fake)
        self.assertEqual(line, b'other line\r\n')
        line = hget.read_line(fake)
        self.assertEqual(line, b'')

    def test_read_line_incomplete(self):
        fake = FakeSocket('text line')
        line = hget.read_line(fake)
        self.assertEqual(line, b'text line')

    def test_get_response(self):
        response = "HTTP/1.0 200 OK\r\n" \
                   "Encabezado: ignorado\r\n" \
                   "Otro: tambien deberia ser ignorado\r\n" \
                   "\r\n" \
                   "dato123456\n" \
                   "7890"
        hget.get_response(FakeSocket(response), TEMPFILE)
        f = open(TEMPFILE)
        self.assertEqual(f.read(), "dato123456\n7890")
        f.close()

    def tearDown(self):
        try:
            os.remove(TEMPFILE)
        except OSError:
            pass

    def test_unicode_url(self):
        socket_connection = hget.connect_to_server("www.ñandú.cl")
        self.assertEqual("200.1.123.10", socket_connection.getpeername()[0])
        socket_connection.close()


if __name__ == "__main__":
    unittest.main()
