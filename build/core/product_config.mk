Import('BUILD_SYSTEM', '_p', '_inc', '_get_var_by_product')
Import('SRC_TARGET_DIR', 'TARGET_PRODUCT')

_inc(BUILD_SYSTEM, 'product.mk')

Import('get_all_product_makefiles')

_inc(SRC_TARGET_DIR, 'product/MiProducts.mk')

for product_file in get_all_product_makefiles():
    _inc(product_file)

TARGET_DEVICE = _get_var_by_product(TARGET_PRODUCT, 'PRODUCT_DEVICE')

Export('TARGET_DEVICE')
