from .meta import GeographyAbc, KnownDefaultsAbc


class KnownDefaultsClasswork(KnownDefaultsAbc):
    ParamClass = 0
    PackageClass = 1


class ClassworkGeo(GeographyAbc):
    ons_nation = 0
    ons_region = 1
    ons_ua = 2
    ons_ltla = 3
    ons_msoa = 4
