.. _faq:

==========================
Frequently Asked Questions
==========================

This FAQ serves two purposes. Firstly, it does what a FAQ generally does --
answer frequently asked questions. Secondly, it is also a place to dump
fragments of documentation which haven't matured enough to be moved into
their own documentation file.



Should I extend the builtin modules and contents, or should I write my own?
===========================================================================

The answer is, as often, the nearly useless "It depends". The built-in modules
serve two purposes: On one hand, they should be ready to use and demonstrate
the power of FeinCMS. On the other hand, they should be simple enough to serve
as examples for you if you want to build your own CMS-like system using the
tools provided by FeinCMS.

If a proposed feature greatly enhances the modules' or content types'
abilities without adding heaps of code, chances are pretty good that it will
be accepted into FeinCMS core. Anyway, the tools included should be so easy
to use that you might still want to build your own page CMS, if your needs
are very different from those of the original authors. If you don't like
monkey patching at all, or if the list of extensions you want to use grows
too big, it might be time to reconsider whether you really want to use the
extension mechanism or if it might not be easier to start freshly, only
using the editor admin classes, feincms.models.Base and maybe parts of the
included PageManager...
