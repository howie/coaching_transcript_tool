import { NextRequest, NextResponse } from 'next/server'

/**
 * Handle ECPay OrderResultURL callback
 * ECPay sends POST data to this endpoint after payment processing
 */
export async function POST(request: NextRequest) {
  try {
    // Parse the form data from ECPay callback
    const formData = await request.formData()
    
    // Extract ECPay callback parameters
    const rtnCode = formData.get('RtnCode') as string
    const rtnMsg = formData.get('RtnMsg') as string
    const merchantMemberId = formData.get('MerchantMemberID') as string
    const merchantTradeNo = formData.get('MerchantTradeNo') as string
    const checkMacValue = formData.get('CheckMacValue') as string
    
    // Log the callback for debugging (don't log sensitive data in production)
    console.log('ECPay OrderResultURL callback received:', {
      rtnCode,
      rtnMsg,
      merchantMemberId,
      merchantTradeNo,
      checkMacValue: checkMacValue ? checkMacValue.substring(0, 10) + '...' : 'missing',
      timestamp: new Date().toISOString()
    })
    
    // Convert POST data to query parameters for frontend display
    const searchParams = new URLSearchParams()
    if (rtnCode) searchParams.set('RtnCode', rtnCode)
    if (rtnMsg) searchParams.set('RtnMsg', rtnMsg)
    if (merchantMemberId) searchParams.set('MerchantMemberID', merchantMemberId)
    if (merchantTradeNo) searchParams.set('MerchantTradeNo', merchantTradeNo)
    
    // Determine the base URL for redirect with fallbacks
    const baseUrl = request.nextUrl.origin || 
                   `${request.nextUrl.protocol}//${request.nextUrl.host}` ||
                   'http://localhost:3000'
    const redirectPath = `/subscription/result?${searchParams.toString()}`
    
    console.log('ECPay callback redirect details:', {
      origin: request.nextUrl.origin,
      protocol: request.nextUrl.protocol,
      host: request.nextUrl.host,
      baseUrl,
      redirectPath,
      fullUrl: `${baseUrl}${redirectPath}`
    })
    
    // Redirect to the subscription result page with query parameters
    return NextResponse.redirect(new URL(redirectPath, baseUrl), {
      status: 302,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    })
    
  } catch (error) {
    console.error('Error processing ECPay OrderResultURL callback:', error)
    
    // Redirect to error state on the subscription result page with fallbacks
    const baseUrl = request.nextUrl.origin || 
                   `${request.nextUrl.protocol}//${request.nextUrl.host}` ||
                   'http://localhost:3000'
    const errorPath = '/subscription/result?RtnCode=0&RtnMsg=Processing%20Error'
    
    return NextResponse.redirect(new URL(errorPath, baseUrl), {
      status: 302,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate'
      }
    })
  }
}

/**
 * Handle GET requests (in case ECPay or users access this endpoint directly)
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const rtnCode = searchParams.get('RtnCode')
  
  console.log('GET request to subscription result API:', {
    searchParams: searchParams.toString(),
    timestamp: new Date().toISOString()
  })
  
  // Redirect GET requests to the page with existing parameters
  const baseUrl = request.nextUrl.origin || 
                 `${request.nextUrl.protocol}//${request.nextUrl.host}` ||
                 'http://localhost:3000'
  const redirectPath = `/subscription/result?${searchParams.toString()}`
  
  return NextResponse.redirect(new URL(redirectPath, baseUrl), { status: 302 })
}