import re
import hashlib
import unicodedata
from keyword import iskeyword

def to_dict(model_instance):
    return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}

def create_valid_function_name(clean_name):
    ascii_normalized_name = unicodedata.normalize('NFKD', clean_name).encode('ASCII', 'ignore').decode()
    
    # Normalize the name
    normalized_name = ascii_normalized_name.lower()
    # Replace spaces and invalid characters with underscores
    function_name = re.sub(r'\W|^(?=\d)', '_', normalized_name)
    # Ensure it starts with a valid character
    if not function_name[0].isalpha():
        function_name = "_" + function_name
        
    unique_identifier = hashlib.md5(clean_name.encode()).hexdigest()[:8]
    function_name += "_" + unique_identifier
    
    if iskeyword(function_name):
        function_name += "_"

    return function_name
