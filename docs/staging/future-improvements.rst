Unistream 未来改进计划
==============================================================================
本文档记录了对 unistream 库设计和实现的审视结果, 列出了需要改进的问题及改进方向.
每个 section 聚焦一个独立的问题.


1. 添加 async/await 支持
------------------------------------------------------------------------------

**为什么需要改进:**

整个库目前是纯同步的. ``consumer.run()`` 使用 ``time.sleep()``, ``send()`` 是同步调用.
现代流处理系统 (Kafka consumer, Kinesis 的 HTTP2 push, Pulsar 的异步 client 等)
几乎都需要异步 I/O. 如果用户想在 asyncio 事件循环中使用 (比如 FastAPI, aiohttp 应用),
这个库无法集成.

**哪里不好:**

- ``consumer.py`` 中 ``run()`` 方法的 ``while 1 + time.sleep()`` 模式会阻塞整个事件循环
- ``producer.py`` 中 ``send()`` 是同步调用, 网络 I/O 期间线程被阻塞
- 没有提供任何异步版本的抽象基类

**改进方向:**

- 提供 ``AsyncAbcProducer``, ``AsyncAbcConsumer`` 等异步版本的抽象基类
- 或采用同步/异步双模式设计, 参考 ``httpx`` 的 ``Client`` / ``AsyncClient`` 模式
- Consumer 的 ``run()`` 应有对应的 ``async def arun()``


2. 支持并行消费
------------------------------------------------------------------------------

**为什么需要改进:**

``_process_batch_in_sequence()`` 是唯一的处理路径. 但对于 Kafka 这种按 partition
并行消费的系统, 顺序处理在性能上不可接受. 更矛盾的是, Checkpoint 的 UUID lock 机制
(``is_record_locked()``) 明显是为并行处理设计的, 但消费端却没有实现并行路径.

**哪里不好:**

- ``consumer.py:202`` 只有 ``_process_batch_in_sequence``, 没有并行版本
- 已经设计了 lock 机制却没有被使用, 代码和设计意图不一致
- I/O 密集型的 record 处理场景下, 顺序处理浪费大量等待时间

**改进方向:**

- 实现 ``_process_batch_in_parallel()`` 方法, 使用线程池或 asyncio 并行处理
- 让用户可以选择顺序或并行模式 (通过参数或子类)
- 并行模式下正确使用已有的 UUID lock 机制


3. Record 序列化应支持 bytes 类型
------------------------------------------------------------------------------

**为什么需要改进:**

``AbcRecord.serialize() -> str`` 强制序列化为字符串. 但 Kafka 和 Kinesis 原生使用
``bytes``, protobuf/avro/msgpack 等高效序列化格式也输出 ``bytes``. 强制 str 意味着
二进制数据需要额外 base64 编码, 浪费空间和性能.

**哪里不好:**

- ``abstraction.py:61`` 中 ``serialize()`` 返回类型硬编码为 ``str``
- ``abstraction.py:69`` 中 ``deserialize()`` 输入类型也硬编码为 ``str``
- FileBuffer 的 WAL 写入也依赖 str 序列化

**改进方向:**

- 将 ``serialize`` 返回类型改为 ``str | bytes``, 或使用泛型 ``T_SERIALIZED``
- ``deserialize`` 的输入类型也要对应调整
- Buffer 的持久化逻辑需要同时支持 str 和 bytes 模式


4. 添加 back-pressure 机制
------------------------------------------------------------------------------

**为什么需要改进:**

Producer 的 ``put()`` 永远立刻接受 record 进 buffer. 如果上游生产速率远高于下游消费速率
(比如 send 持续失败), buffer 的 WAL 文件会无限增长, 最终耗尽磁盘空间. 调用方没有任何
方式知道系统已经过载.

**哪里不好:**

- ``producer.py`` 的 ``_put()`` 方法无条件调用 ``self.buffer.put(record)``
- ``AbcBuffer`` 没有 "容量已满, 拒绝写入" 的语义
- 没有流量控制的反馈通道

**改进方向:**

- Buffer 添加总容量上限 (跨 batch 的), 达到上限时 ``put()`` 阻塞或抛出 ``BufferFullError``
- 或 ``put()`` 返回 ``Future`` 对象, 让调用方可以感知发送结果和背压状态
- 提供 buffer 使用率的查询接口 (如 ``buffer.usage_ratio()``)


5. 添加 graceful shutdown 机制
------------------------------------------------------------------------------

**为什么需要改进:**

Consumer 的 ``run()`` 是 ``while 1`` 无限循环, 没有退出机制. Producer 没有 ``flush()``
方法. 用户只能 kill 进程然后靠 checkpoint 恢复, 但这正是库试图避免的数据丢失场景.

**哪里不好:**

- ``consumer.py:243`` ``while 1`` 没有 stop flag, 没有 signal handler
- Producer 没有 ``flush()`` 方法, buffer 中残留的 records 在进程退出时会丢失
  (虽然有 WAL, 但需要等下次启动才能恢复)
- 没有 context manager 协议 (``__enter__`` / ``__exit__``)

**改进方向:**

- Consumer 添加 ``stop()`` 方法和内部 stop flag, ``run()`` 循环中检查 flag
- Producer 添加 ``flush()`` 方法, 强制发送 buffer 中所有残留 records
- Producer 和 Consumer 都实现 context manager 协议, 退出时自动 flush/commit
- 注册 ``SIGTERM`` / ``SIGINT`` handler 进行 graceful shutdown


6. 统一 retry 机制
------------------------------------------------------------------------------

**为什么需要改进:**

Producer 和 Consumer 使用两套完全不同的 retry 机制:
Producer 用自研的 ``RetryConfig`` (基于时间戳比较),
Consumer 用 tenacity 的 ``@retry`` 装饰器.
API 风格和语义不一致, 增加了理解和维护成本.

**哪里不好:**

- ``producer.py`` 的 ``RetryConfig`` 是自研的时间戳比较逻辑
- ``consumer.py:169-177`` 每次调用 ``_process_record()`` 都重新创建 tenacity retry 装饰器, 有不必要的对象创建开销
- 两套 retry 的配置参数名完全不同, 用户需要学习两种配置方式

**改进方向:**

- 统一使用一套 retry 机制 (tenacity 或自研, 选择一个)
- 如果保留两套, 至少统一配置接口 (如共用一个 ``RetryPolicy`` 类)
- Consumer 中的 retry 装饰器应该只创建一次, 而非每次调用都创建


7. 修复 timedelta(expire) bug
------------------------------------------------------------------------------

**为什么需要改进:**

这是一个实际存在的 bug, 会导致 lock 过期时间计算错误.

**哪里不好:**

``checkpoint.py:218``::

    tracker.lock_expire_time = (now + timedelta(expire)).isoformat()

``timedelta(expire)`` 等价于 ``timedelta(days=expire)``. 如果 ``lock_expire`` 是
900 (秒), 这里实际设置的是 900 **天** 后过期, 而非 900 秒. lock 永远不会过期.

**改进方向:**

改为 ``timedelta(seconds=expire)``.


8. AbcCheckPoint 的方法应使用 @abc.abstractmethod
------------------------------------------------------------------------------

**为什么需要改进:**

``AbcCheckPoint`` 的方法 (``dump``, ``load``, ``mark_as_*``, ``dump_as_*``)
只是 ``raise NotImplementedError``, 没有标注 ``@abc.abstractmethod``. 这与其他四个
ABC (``AbcRecord``, ``AbcBuffer``, ``AbcProducer``, ``AbcConsumer``) 的设计不一致.

**哪里不好:**

- ``abstraction.py:314-448`` 中 ``AbcCheckPoint`` 的所有方法都缺少 ``@abc.abstractmethod``
- 这意味着可以实例化一个不完整的子类而不会在类定义时报错, 只会在运行时发现
- 降低了类型检查器和 IDE 的错误检测能力

**改进方向:**

对 ``AbcCheckPoint`` 中需要子类实现的方法添加 ``@abc.abstractmethod`` 装饰器.
注意: ``mark_as_*`` 方法在 ``BaseCheckPoint`` 中有实现, 所以只需要对
``dump``, ``load``, ``dump_records``, ``load_records``, ``dump_as_*`` 添加.


9. 增加类型安全性
------------------------------------------------------------------------------

**为什么需要改进:**

多处设计丢失了类型信息, 增加了运行时错误的可能性.

**哪里不好:**

- ``T_POINTER = str | int`` 太宽泛, 无法约束同一个 Checkpoint 实例内 pointer 类型一致
- ``AbcBuffer`` 声明了 ``max_records`` 和 ``max_bytes`` 属性但不是构造参数, 子类可以不设置
- 所有 ``new()`` 工厂方法使用 ``**kwargs``, 完全丢失了类型信息, IDE 无法提供补全和检查

**改进方向:**

- ``BaseCheckPoint`` 使用泛型 ``Generic[T_POINTER]`` 约束 pointer 类型
- ``new()`` 工厂方法使用显式参数签名替代 ``**kwargs``
- ``AbcBuffer`` 将 ``max_records`` / ``max_bytes`` 定义为 ``@abc.abstractmethod`` property 或构造参数


10. 支持 partition/shard 概念
------------------------------------------------------------------------------

**为什么需要改进:**

Kafka 有 partition, Kinesis 有 shard, Pulsar 有 topic partition. 当前设计是单流单
checkpoint. 如果要消费一个有 8 个 partition 的 Kafka topic, 用户需要自己管理 8 个
Consumer 实例和 8 个 Checkpoint, 抽象层完全没有帮助.

**哪里不好:**

- ``AbcConsumer`` 和 ``AbcCheckPoint`` 没有 partition/shard 的概念
- 单 checkpoint 只跟踪单个 pointer, 无法表达多 partition 的消费进度
- 实际使用时, 用户需要在库的外部自行编排多个 consumer 实例

**改进方向:**

- 在 Checkpoint 中支持多 pointer (如 ``dict[str, T_POINTER]`` 按 partition 跟踪)
- 或引入 ``PartitionAssigner`` / ``ShardCoordinator`` 抽象, 管理多分区的分配
- Consumer 支持同时消费多个 partition, 每个 partition 有独立的 checkpoint


11. 支持 push 模式消费
------------------------------------------------------------------------------

**为什么需要改进:**

整个 Consumer 设计围绕 "pull batch -> process -> commit" 循环. 但很多系统使用
push 模式: WebSocket, gRPC streaming, GCP Pub/Sub push subscription, AWS SNS.
当前的 ``get_records()`` 抽象无法表达 push 模式.

**哪里不好:**

- ``AbcConsumer.get_records()`` 假设消费者主动拉取数据
- ``BaseConsumer.run()`` 的 poll 循环模式与 push 语义不兼容
- 如果要支持 push 模式, 用户需要完全绕过库的消费循环, 只用 checkpoint 功能

**改进方向:**

- 考虑引入 ``on_records(records, next_pointer)`` 回调式接口, 让 push 系统可以主动
  把数据推给 consumer
- 或将消费循环和 record 处理逻辑解耦, 让用户可以自己控制数据获取方式,
  只使用库提供的 checkpoint + process + retry 能力


12. 添加 schema 版本控制
------------------------------------------------------------------------------

**为什么需要改进:**

Record 的 ``serialize/deserialize`` 没有版本号. 当 Record 结构发生变化时
(加字段, 删字段, 改类型), WAL 文件和 checkpoint 备份中的旧数据无法正确反序列化.
在生产环境中 schema 演化是非常常见的问题.

**哪里不好:**

- ``AbcRecord`` 没有 schema version 属性或机制
- ``DataClassRecord.deserialize()`` 直接 ``json.loads`` 然后实例化, 不处理字段不匹配
- WAL 文件和 checkpoint records 文件中的旧格式数据会导致反序列化失败

**改进方向:**

- 在 Record 序列化中嵌入 schema version (如 ``{"_v": 1, ...}``)
- 提供 migration hook 让用户定义版本间的转换逻辑
- 或在文档中给出 schema 演化的最佳实践 (如使用 ``Optional`` 字段 + 默认值)


13. 添加 metrics / observability hook
------------------------------------------------------------------------------

**为什么需要改进:**

没有暴露任何 metrics 接口. 在生产环境中, 可观测性数据 (throughput, retry count,
buffer size, processing latency) 比 emoji 日志重要得多. 当前只有 ``vislog`` 输出,
无法集成到 Prometheus, StatsD, OpenTelemetry 等监控系统.

**哪里不好:**

- 没有任何 metrics 收集点
- 没有 event hook 让用户注入自定义的监控逻辑
- ``vislog`` 的 emoji 日志只适合开发调试, 不适合生产监控

**改进方向:**

- 在关键路径暴露 callback hook (如 ``on_send_success``, ``on_send_failure``,
  ``on_record_processed``, ``on_batch_committed``)
- 或提供一个 ``MetricsCollector`` 接口, 让用户实现并注入
- 内置一些基础 metrics (buffer 大小, retry 次数, 处理延时) 的记录


14. 精确 exactly-once 语义的表述
------------------------------------------------------------------------------

**为什么需要改进:**

文档中多次提到 "exactly-once consumption", 但实际实现只能做到
"at-least-once + 幂等检查". 真正的 exactly-once 需要在 send 和 checkpoint 之间有
事务保证 (如 Kafka 的 transactional producer). 当前实现中, 如果 ``send()`` 成功但
``buffer.commit()`` 前 crash, 重启后会重发, 这不是 exactly-once.

**哪里不好:**

- 文档中 "Exact-once consumption" 的措辞可能误导用户
- 实际保证的是 at-least-once delivery + per-record status tracking (辅助幂等)
- 没有事务性的 send + commit 原子操作

**改进方向:**

- 文档中将语义精确描述为 "at-least-once with idempotency support"
- 如果要支持真正的 exactly-once, 需要引入 transactional commit 抽象
  (send + checkpoint update 作为原子操作)
- 至少在文档中说明 exactly-once 的前提条件和局限性


15. Consumer 中 _process_record 的状态管理问题
------------------------------------------------------------------------------

**为什么需要改进:**

``_process_record()`` 中存在绕过 checkpoint API 直接修改状态的代码,
导致状态管理逻辑分散且 attempts 计数可能不准确.

**哪里不好:**

``consumer.py:167``::

    self.checkpoint.batch[record.id].status = StatusEnum.in_progress.value

这行直接修改了 tracker 的 status, 绕过了 ``mark_as_in_progress()`` 方法.
然后在 ``_process_record_with_checkpoint()`` 中又调用了 ``mark_as_in_progress()``,
导致:

- ``attempts`` 在每次 tenacity retry 时通过 ``mark_as_in_progress`` 递增,
  但外层已经独立设置了状态
- 状态更新逻辑分散在两个方法中, 增加了理解和维护的难度
- 如果未来修改 ``mark_as_in_progress`` 的逻辑, 这里的直接赋值不会同步更新

**改进方向:**

- 移除 ``consumer.py:167`` 的直接状态修改, 统一通过 ``mark_as_in_progress()`` 管理
- 或重新设计 ``_process_record`` 和 ``_process_record_with_checkpoint`` 的职责边界,
  避免两层方法都操作 checkpoint 状态
