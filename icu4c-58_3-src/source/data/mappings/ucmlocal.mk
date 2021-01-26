################################################################################
#
# TITLE: ucmlocal.mk
#
#   Copyright 2004-2011, TERADATA Corporation.  ALL RIGHTS RESERVED.
#   TERADATA PROPRIETARY AND CONFIDENTIAL-RESTRICTED.
#
#
#  Purpose:     To add additional converters for Teradata UTF-16 conversions
#
# Revision    Date     DR    DID      Comments
# ----------- -------- ----- -------- ------------------------------------------
# 01.00.00.00 07222004 88707 pop      Initial Version
# 01.01.01.00 05272005 95564 Bill     Update the copyright
# 14.00.00.00 01282011 148220SE185013 Support for TD Added Site-Defined Charsets
#
#  * To add an additional converter to the list:
#    _____________________________________________________
#    |  UCM_SOURCE_LOCAL =  myconverter.ucm ...
#
################################################################################

UCM_SOURCE_LOCAL = td_ebcdic.ucm \
td_ebcdic037_0e.ucm        \
td_ebcdic273_0e.ucm        \
td_ebcdic277_0e.ucm        \
td_hangulebcdic933_1ii.ucm \
td_hangulksc5601_2r4.ucm   \
td_kanjiebcdic5026_0i.ucm  \
td_kanjiebcdic5035_0i.ucm  \
td_kanjieuc_0u.ucm         \
td_kanjisjis_0s.ucm        \
td_katakanaebcdic.ucm      \
td_latin1252_0a.ucm        \
td_latin1_0a.ucm           \
td_latin9_0a.ucm           \
td_schebcdic935_2ij.ucm    \
td_schgb2312_1t0.ucm       \
td_tchbig5_1r0.ucm         \
td_tchebcdic937_3ib.ucm    \
td_hangul949_7r0.ucm       \
td_schinese936_6r0.ucm     \
td_tchinese950_8r0.ucm

