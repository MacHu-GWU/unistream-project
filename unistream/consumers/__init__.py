# -*- coding: utf-8 -*-

"""
[CN] Maintainer Note

在这个目录下的模块是各种针对特定 Stream system 的 Consumer 的具体实现. 对于不同的应用场景,
用户需要继承这些 Consumer, 并且实现其中的
:class:`unistream.abstraction.AbcConsumer.process_record`
和 :class:`unistream.abstraction.AbcConsumer.process_failed_record` 方法.
"""
