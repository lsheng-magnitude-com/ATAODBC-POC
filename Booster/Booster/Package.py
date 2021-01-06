from __future__ import print_function
import fileinput
import os

import ata.log

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('      Enter Package')
    print('==============================')

    brandingFile = getBrandingFile(root)
    brandingSettings = loadBrandingFile(brandingFile)
    setBrandinginfo(brandingSettings, root)

def Debug(root):
    print('==============================')
    print('      Enter Package')
    print('==============================')

    brandingFile = getBrandingFile(root)
    brandingSettings = loadBrandingFile(brandingFile)
    logger.info('brandingSettings = ' + str(brandingSettings))

def getBrandingFile(root):
    brandingFile = root.attrib.get('brand', 'undef')
    return brandingFile


def loadBrandingFile(file):
    logger.info('load ' + file)
    brandingSettings = {}
    product = os.environ.get('BOOSTER_VAR_PRODUCT', '')
    brand = os.environ.get('BOOSTER_VAR_DRV_BRAND', os.environ.get('bamboo_DRV_BRAND',''))
    logger.info('Set branding info for ' + brand)
    brandingSettings['PRODUCT'] = product
    brandingSettings['PRODUCT_LOWER'] = product.lower()
    brandingSettings['PRODUCT_UPPER'] = product.upper()
    brandingSettings['DRV_BRAND'] = brand
    brandingSettings['DRV_BRAND_LOWER'] = brand.lower()
    brandingSettings['DRV_BRAND_UPPER'] = brand.upper()
    if os.path.exists(file):
        f = fileinput.FileInput(file)
        for line in f:
            if ('=' in line):
                settingArray = line.split('=', 1)
                brandingSettings[settingArray[0]] = settingArray[1].rstrip()
                brandingSettings[settingArray[0] + '_LOWER'] = settingArray[1].rstrip().lower()
                brandingSettings[settingArray[0] + '_UPPER'] = settingArray[1].rstrip().upper()
            else:
                continue
        f.close()
        # for key in brandingSettings.keys():
        #     print(key + ':' + brandingSettings[key])
    else:
        logger.info('branding config file does not exist')
    return brandingSettings


def setBrandinginfo(brandingSettings, root):
    for var in brandingSettings.keys():
        val = brandingSettings[var]
        os.environ[var] = val
        varName = '$(' + var + ')'
        varValue = val
        for element in root.iter():
            if (varName in element.text):
                oldText = element.text
                newText = oldText.replace(varName, varValue)
                element.text = newText
            if (varName in str(element.attrib)):
                for key in element.attrib.keys():
                    oldText = element.attrib[key]
                    newText = oldText.replace(varName, varValue)
                    element.attrib[key] = newText
