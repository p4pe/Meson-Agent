from cerberus import Validator
import yaml

ProvSchema = {
    'appD': {
        'required': True,
        'type': 'dict',
        'schema': {
            'appID': {'required': True, 'type': 'integer'},
            'appName': {'required': True, 'type': 'string'},
            'appProvider': {'required': True, 'type': 'string'},
            'PoPID': {'required': True, 'type': 'string'},
            'PoPKPIs': {'required': False, 'type':'dict',
                'schema':{
                    'Availability_Zone':{'required': False, 'type': 'integer'},
                    'CSC_Service_Catalog':{'required': False, 'type': 'integer'},
                    'Elasticity':{'required': False, 'type': 'integer'},
                    'VM_Cost':{'required': False, 'type': 'integer'},
                    'Availability':{'required': False, 'type': 'integer'},
                    'Service_Response':{'required': False, 'type': 'integer'},
                    'Bandwidth':{'required': False, 'type': 'integer'},
                    'Data_Cost':{'required': False, 'type': 'integer'},
                    'Document_Readability':{'required': False, 'type': 'integer'},
                    'Technical_Support':{'required': False, 'type': 'integer' }
                         }, #this comma might not be needed
                       },
            'appServiceProduced': {'required': False, 'type': 'dict',
                'schema': {
                    'nsd_ref_name': {'required': True, 'type': 'string'},
                    'member_vnf_index': {'required': True, 'type': 'integer'},
                    'serName': {'required': True, 'type': 'string'},
                    'CSC_VNF': {'required': False, 'type': 'list',
                        'schema': { 'type': 'dict',
                            'schema': {
                                'vnfdName': {'required': True, 'type': 'string'},
                                'seq_no': {'required': True, 'type': 'integer'},
                                'direction': {'required': True, 'type': 'integer', 'allowed': [0, 1]}
                                      }
                                  }
                               },
                    "PeerPolicy":{'required': True, 'type': 'dict',
                        'schema':{
                            'ID': {'required': True, 'type': 'string'},
                            'depProfile': {'required': True, 'type': 'dict',
                                'schema': {
                                    'bandwidth':{'required': True, 'type': 'integer'},
                                    'cpu':{'required': True, 'type': 'integer'},
                                    'memory':{'required': True, 'type': 'integer'},
                                    'storage': {'required': True, 'type': 'integer'},
                                    'latency': {'required': True, 'type': 'integer'}
                                          }
                                          },
                            'scaleOut':{'required': True, 'type': 'boolean'}
                                 }
                                  }#PEER POLICY
                                }
                            }#APP SERVICE PRODUCED
                }
            }
        }


ConsSchema = {
'appDC': {
        'required': True,
        'type': 'dict',
        'schema': {
            'appID': {
                'required': True,
                'type': 'integer'
            },
            'appName': {
                'required': True,
                'type': 'string'
            },
            'appProvider': {
                'required': True,
                'type': 'string'
            },
            'PoP_Preferences':{
                'required': True,
                'type': 'dict',
                'schema': {
                    'Cost': {
                        'required': True,
                        'type': 'float'

                    },
                    'Computing_Performance':{
                        'required': True,
                        'type': 'float'
                    },
                    'Network_Performance':{
                      'required': True,
                      'type': 'float'
                    },
                    'Pref_Location': {
                        'required': True,
                        'type': 'string'
                    },
                },
            },
             'appServiceRequired': {
                 'required': True,
                 'type':'dict',
                 'schema':{
                    'nsd_ref_name': {
                         'required': True,
                         'type': 'string'
                     },
                    'member_vnf_index': {
                         'required': True,
                         'type': 'integer'
                     },
                     'serName': {
                         'required': True,
                         'type': 'string'
                     },
                     'depProfile':{
                         'required': True,
                         'type': 'dict',
                         'schema':{
                             'bandwidth':{
                                 'required': True,
                                 'type': 'integer'
                             },
                             'cpu':{
                                 'required': True,
                                 'type':'integer'
                             },
                             'memory':{
                                 'required': True,
                                 'type': 'integer'
                             },
                             'storage':{
                                 'required': True,
                                 'type': 'integer'
                             },
                             'latency':{
                                 'required': True,
                                 'type': 'integer'
                             }
                         }
                     }

             }
            }

}
}
}
