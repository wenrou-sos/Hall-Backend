package player

import (
    "sync"
)

type bufferPool struct {
    pool *sync.Pool
}

func newBufferPool() *bufferPool {
    return &bufferPool{
        &sync.Pool{},
    }
}

func (b *bufferPool) Get() (data interface{}) {
    return b.pool.Get()
}

func (b *bufferPool) Put(data interface{}) {
    b.pool.Put(data)
}
