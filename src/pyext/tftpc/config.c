#include "config.h"

char *xstrdup(const char *str)
{
    return strcpy (xmalloc (strlen (str) + 1), str);
}
char *xmalloc(size_t n)
{
    return (malloc ((unsigned)n));
}