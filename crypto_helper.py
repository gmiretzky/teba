"""
This module provides crypto functions for encryption , decryption and hashing.
"""
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoHelper:
	"""Static class to provide crypto functions"""
	@staticmethod
	def hash(stext, ltimes=1):
		"""This function Hash the input text (stext) number of times (ltime)"""
		ctext = stext
		for _ in range(ltimes):
			hash_object = hashlib.sha512(ctext.encode())
			ctext = hash_object.hexdigest()
		return hash_object.hexdigest()
	@staticmethod
	def encrypt(password, message):
		"""This function return the encrypted text of the provided text (message)
		using the key (password)"""
		kdf = PBKDF2HMAC(
			algorithm=hashes.SHA256(),
			length=32,
			salt=b"salt",
			iterations=100000,
			backend=default_backend()
		)
		key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
		token = Fernet(key)
		return token.encrypt(message.encode())
	@staticmethod
	def decrypt(password, message):
		"""This function return the decryption of the text of the provided text (message)
		using the key (password)"""
		kdf = PBKDF2HMAC(
			algorithm=hashes.SHA256(),
			length=32,
			salt=b"salt",
			iterations=100000,
			backend=default_backend()
		)
		key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
		token = Fernet(key)
		return token.decrypt(message).decode('ascii')
