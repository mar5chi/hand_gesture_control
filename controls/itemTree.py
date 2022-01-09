
itemTree = {
    'kitchen' : {		# ONE
        'light' : {
            'item1' : {
                'name' : 'Kueche1_KNX_Licht_Schalten',
                'type' : 'bool',             # ON or OFF
                'label' : 'dinner table light'
            },
            'item2' : {
                'name' : 'Kueche2_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'cooking table light'
            },
            'item3' : {
                'name' : 'Kueche_LichtDimmer',
                'type' : 'percentage',       # 0 - 100
                'label' : 'dimmer'
            },
            'item4' : {
                'name' : 'LED_On_Off',
                'type' : 'bool',
                'label' : 'L E D switch'
            },
            'item5' : {
                'name' : 'LED_ColorTemp',
                'type' : 'percentage',
                'label' : 'L E D Color Temp'
            }
        },
        'blind' : {
            'blind1' : {
                'name' : 'Kuche_Jalousie1',
                'type' : 'percentage',
                'label' : 'blind 1'
            },
            'blind2' : {
                'name' : 'Kuche_Jalousie2',
                'type' : 'percentage',
                'label' : 'blind 2'
            }
        }
    },
    'livingroom' : {	# TWO
        'light' : {
            'item1' : {
                'name' : 'WZ_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'switch'
            },
            'item2' : {
                'name' : 'WZ_LichtDimmer',
                'type' : 'percentage',
                'label' : 'dimmer'
            }
        },
        'blind' : {
            'blind1' : {
                'name' : 'Wohnzimmer_Jalousie1',
                'type' : 'percentage',
                'label' : 'blind 1'
            },
            'blind2' : {
                'name' : 'Wohnzimmer_Jalousie2',
                'type' : 'percentage',
                'label' : 'blind 2'
            },
            'blinds' : {    # 3
                'name' : 'WZ_Jalousien',
                'type' : 'percentage',
                'label' : 'livingroom blinds'
            }
        }
    },
    'bedroom' : {		# THREE
        'light' : {
            'item1' : {
                'name' : 'Schlafzimmer_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'switch'
            },
            'item2' : {
                'name' : 'SZ_LichtDimmer',
                'type' : 'percentage',
                'label' : 'dimmer'
            }
        }
    },
    'seminarroom' : { 	# FOUR
        'light' : {
            'item1' : {
                'name' : 'SR_LichtDimmer',
                'type' : 'percentage',
                'label' : 'dimmer'
            },
            'item2' : {
                'name' : 'SR_Beamerseite',
                'type' : 'percentage',
                'label' : 'dimmer projector side'
            },
            'item3' : {
                'name' : 'SR_Kuechenseite',
                'type' : 'percentage',
                'label' : 'dimmer kitchen side'
            }
                    
        },
        'blind' : {
            'blind1' : {
                'name' : 'Seminarraum_Jalousie1',
                'type' : 'percentage',
                'label' : 'blind 1'
            },
            'blind2' : {
                'name' : 'Seminarraum_Jalousie2',
                'type' : 'percentage',
                'label' : 'blind 2'
            }
        }
    },
    'iot_lab' : { 		# FIVE
        'light' : {
            'item1' : {
                'name' : 'IoT_LichtDimmer',
                'type' : 'percentage',
                'label' : 'dimmer'
            },
            'item2' : {
                'name' : 'IoT_Beamer',
                'type' : 'percentage',
                'label' : 'dimmer projector'
            },
            'item3' : {
                'name' : 'IoT_Ecke',
                'type' : 'percentage',
                'label' : 'dimmer corner'
            },
            'item4' : {
                'name' : 'IoT_Buero',
                'type' : 'percentage',
                'label' : 'dimmer office'
            },
            'item5' : {
                'name' : 'Szenen_IoT',
                'type' : 'percentage',
                'label' : 'scenes'
            }
        },
        'blind' : {
            'blind1' : {
                'name' : 'IoT_Jalousie1',
                'type' : 'percentage',
                'label' : 'blind 1'
            },
            'blind2' : {
                'name' : 'IoT_Jalousie2',
                'type' : 'percentage',
                'label' : 'blind 1'
            },
            'blind3' : {
                'name' : 'IoT_Jalousie3',
                'type' : 'percentage',
                'label' : 'blind 1'
            },
            'blind4' : {
                'name' : 'IoT_Jalousie4',
                'type' : 'percentage',
                'label' : 'blind 1'
            }
        }
    },
    'bathroom' : {		# SIX
        'light' : {
            'item1' : {
                'name' : 'Bad_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'switch'
            },
            'item2' : {
                'name' : 'Bad_Tuer',
                'type' : 'bool',
                'label' : 'door'
            }
        }
    },
    'bathroom2' : {		# SEVEN currently just as placeholder
        'light' : {
            'item1' : {
                'name' : 'Bad_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'switch'
            },
            'item2' : {
                'name' : 'Bad_Tuer',
                'type' : 'bool',
                'label' : 'door'
            }
        }
    },
    'bathroom3' : {		# EIGHT currently just as placeholder
        'light' : {
            'item1' : {
                'name' : 'Bad_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'switch'
            },
            'item2' : {
                'name' : 'Bad_Tuer',
                'type' : 'bool',
                'label' : 'door'
            }
        }
    },
    'bathroom4' : {		# NINE currently just as placeholder
        'light' : {
            'item1' : {
                'name' : 'Bad_KNX_Licht_Schalten',
                'type' : 'bool',
                'label' : 'switch'
            },
            'item2' : {
                'name' : 'Bad_Tuer',
                'type' : 'bool',
                'label' : 'door'
            }
        }
    },
    'apartment' : {     # ALOHA (10)
        'light' : {
            'centrallight' : {
                'name' : 'Wohnung_Zentral_ON_OFF',
                'type' : 'bool',
                'label' : 'central switch'
            }
        },
        'blind' : {
            'centralblinds' : {
                'name' : 'Wohnung_Jalousien',
                'type' : 'percentage',
                'label' : 'central blinds'
            }
        },
        'temperature' : {
            'centraltemp' : {
                'name' : 'SOLL_Wohnung_Temp',
                'type' : 'percentage',
                'label' : 'central temperature'
            }
        }
    }
}

# ----------------------------------------------------------------------------------------------------------------
# For testing:
if __name__ == '__main__':
    import json
    
    # test item tree:
    print(str(itemTree))
    # write to JSON
    with open("my.json","w") as f:
        json.dump(itemTree, f, indent=4)  # indent for pretty print
    
    print(itemTree['kitchen']['light']['item1'])
    item = itemTree['kitchen']['light']['item1']
    print(item)
    print(f'name={item["name"]} type={item["type"]}')
    
    area_list = list(itemTree)  # level 1 in dict
    print(area_list)
    a_key = area_list[0]
    print(a_key)
    function_list_area1 = list(itemTree[area_list[0]])
    print(function_list_area1)
    
    list_x = list(itemTree['kitchen']['light'])
    print(f'length of list_x: {len(list_x)}')
    item2_key = list_x[3]
    print(item2_key)
    item2 = itemTree['kitchen']['light'][item2_key]  # is a dict
    print(item2)
    iname = item2['name']
    print(iname)
    itype = item2['type']
    print(itype)
    # Prevent KeyError if key is not in dict:
    ilabel = item2.get('label')
    if ilabel:
        print(ilabel)
    else:
        print('no label')


