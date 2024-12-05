#!/usr/bin/env python
# encoding: utf-8
"""
hget: un cliente HTTP simple

Ejemplo concreto las primitivas básicas de comunicación por sockets. No es para uso en producción.

"""

import sys
import socket
import optparse

PREFIX = "http://"
HTTP_PORT = 80   # El puerto por convencion para HTTP,
# según http://tools.ietf.org/html/rfc1700
HTTP_OK = "200"  # El codigo esperado para respuesta exitosa.


def parse_server(url):
    assert url.startswith(PREFIX)
    # Removemos el prefijo:
    path = url[len(PREFIX):]
    path_elements = path.split('/')
    result = path_elements[0]

    assert url.startswith(PREFIX + result)
    assert '/' not in result

    return result


def connect_to_server(server_name):
    # Buscar direccion ip
    # Aqui deberian obtener la direccion ip del servidor y asignarla
    ip_address = socket.gethostbyname(server_name.encode("idna"))

    # a ip_address
    print(f"Contactando al servidor en {ip_address}...")

    # Crear socket
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Aqui deben conectarse al puerto correcto del servidor
    socket_server.connect((ip_address, HTTP_PORT))
    return socket_server


def send_request(connection, url):
    HTTP_REQUEST = b"GET %s HTTP/1.0\r\n\r\n"

    connection.send(HTTP_REQUEST % url.encode())


def read_line(connection):
    result = b''
    error = False
    # Leer de a un byte
    try:
        data = connection.recv(1)
    except Exception:
        error = True
    while not error and data != b'' and data != b'\n':
        result = result + data
        try:
            data = connection.recv(1)
        except Exception:
            error = True
    if error:
        raise Exception("Error leyendo de la conexion!")
    else:
        result += data  # Add last character
        return result


def check_http_response(header):
    header = header.decode()
    elements = header.split(' ', 3)
    return (len(elements) >= 2 and elements[0].startswith("HTTP/")
            and elements[1] == HTTP_OK)


def get_response(connection, filename):
    BUFFER_SIZE = 4096

    # Verificar estado
    header = read_line(connection)
    if not check_http_response(header):
        sys.stdout.write("Encabezado HTTP malformado: '%s'\n" % header.strip())
        return False
    else:
        # Saltear el resto del encabezado
        line = read_line(connection)
        while line != b'\r\n' and line != b'':
            line = read_line(connection)

        # Descargar los datos al archivo
        output = open(filename, "wb")
        data = connection.recv(BUFFER_SIZE)
        while data != b'':
            output.write(data)
            data = connection.recv(BUFFER_SIZE)
        output.close()
        return True


def download(url, filename):
    # Obtener server
    server = parse_server(url)
    sys.stderr.write("Contactando servidor '%s'...\n" % server)

    try:
        connection = connect_to_server(server)
    except socket.gaierror:
        sys.stderr.write("No se encontro la direccion '%s'\n" % server)
        sys.exit(1)
    except socket.error:
        sys.stderr.write("No se pudo conectar al servidor HTTP en '%s:%d'\n"
                         % (server, HTTP_PORT))
        sys.exit(1)

    # Enviar pedido, recibir respuesta
    try:
        sys.stderr.write("Enviando pedido...\n")
        send_request(connection, url)
        sys.stderr.write("Esperando respuesta...\n")
        result = get_response(connection, filename)
        if not result:
            sys.stderr.write("No se pudieron descargar los datos\n")
    except Exception as e:
        sys.stderr.write(f"Error al comunicarse con el servidor: {e}\n")
        # Descomentar la siguiente línea para debugging:
        raise
        sys.exit(1)


def main():
    # Parseo de argumentos
    parser = optparse.OptionParser(usage="usage: %prog [options] http://...")
    parser.add_option("-o", "--output", help="Archivo de salida",
                      default="download.html")
    options, args = parser.parse_args()
    if len(args) != 1:
        sys.stderr.write("No se indico una URL a descargar\n")
        parser.print_help()
        sys.exit(1)

    # Validar el argumento
    url = args[0]
    if not url.startswith(PREFIX):
        sys.stderr.write("La direccion '%s' no comienza con '%s'\n" % (url,
                                                                       PREFIX))
        sys.exit(1)

    download(url, options.output)


if __name__ == "__main__":
    main()
    sys.exit(0)
