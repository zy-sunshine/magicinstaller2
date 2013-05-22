Import('BUILD_SYSTEM', '_p', '_inc')
Import('SRC_TARGET_DIR')

_inc(BUILD_SYSTEM, 'product.mk')
Import('get_all_product_makefiles')

_inc(SRC_TARGET_DIR, 'product/MiProducts.mk')

for product_file in get_all_product_makefiles():
    _inc(product_file)

