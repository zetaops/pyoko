SOLR_FIELDS = {
'string': '<field name="%s" type="string"  indexed="true" stored="true" multiValued="%s" />',
'int': '<field name="%s" type="int" indexed="true" stored="false" multiValued="%s" />',
'bool': '<field name="deleted" type="boolean" indexed="true" stored="false" multiValued="%s" />',
'local': '<field name="*_tr" type="text_%s" indexed="true" stored="true" multiValued="%s" />'
}
