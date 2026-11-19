//+build dev

package accounting

func (b *builder) SetDB(hostExtId string) *builder {
    b.db = nil
    return b
}
