# Makefile for source rpm: dovecot
# $Id$
NAME := dovecot
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
