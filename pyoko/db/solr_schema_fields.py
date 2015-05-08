SOLR_FIELDS = {
'string': '<field type="string" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />',
'text': '<field type="string"  name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />',
'float': '<field type="float"  name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />',
'int': '<field type="int" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />',
'bool': '<field type="boolean" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />',
'local': '<field type="text_{type}" name="{name}"  indexed="{index}" stored="{store}" multiValued="{multi}" />'
}
