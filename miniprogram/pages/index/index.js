const TEMPLATE_ID = 'ooHic5rLsTcb_uhLMkiUcUSv3VQjHGcmhLC6ipLPXrQ'

Page({
  data: {
    subscribed: false
  },

  onLoad() {
    // 检查本地是否已订阅
    const subscribed = wx.getStorageSync('subscribed')
    this.setData({ subscribed: !!subscribed })
  },

  onSubscribeTap() {
    wx.requestSubscribeMessage({
      tmplIds: [TEMPLATE_ID],
      success: (res) => {
        if (res[TEMPLATE_ID] === 'accept') {
          // 用户同意订阅，获取 openid 并上报
          wx.login({
            success: (loginRes) => {
              // 将 code 发给后端换取 openid
              wx.request({
                url: 'https://rentals-authorization-sufficient-minnesota.trycloudflare.com/subscribe',
                method: 'POST',
                data: {
                  code: loginRes.code,
                  template_id: TEMPLATE_ID
                },
                success: () => {
                  wx.setStorageSync('subscribed', true)
                  this.setData({ subscribed: true })
                  wx.showToast({ title: '订阅成功', icon: 'success' })
                },
                fail: () => {
                  wx.showToast({ title: '订阅失败，请重试', icon: 'none' })
                }
              })
            }
          })
        } else {
          wx.showToast({ title: '已取消订阅', icon: 'none' })
        }
      },
      fail: (err) => {
        console.error('订阅失败', err)
        wx.showToast({ title: '订阅失败', icon: 'none' })
      }
    })
  }
})
