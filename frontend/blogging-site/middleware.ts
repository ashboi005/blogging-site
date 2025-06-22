import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Get tokens from cookies
  const accessToken = request.cookies.get('access_token')?.value
  const refreshToken = request.cookies.get('refresh_token')?.value

  if (!accessToken) {
    // If no access token, try to refresh it
    if (refreshToken) {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Failed to refresh token')
        }

        const newAccessToken = data.access_token
        const responseWithToken = NextResponse.next()
        responseWithToken.cookies.set('access_token', newAccessToken, { path: '/', secure: true, sameSite: 'strict' })
        return responseWithToken

      } catch (error) {
        console.error('Token refresh failed:', error)
        // If refresh fails, redirect to login
        const loginUrl = new URL('/auth', request.url)
        loginUrl.searchParams.set('next', pathname)
        return NextResponse.redirect(loginUrl)
      }
    } else {
      // If no tokens, redirect to login
      const loginUrl = new URL('/auth', request.url)
      loginUrl.searchParams.set('next', pathname)
      return NextResponse.redirect(loginUrl)
    }
  } else {
    // If access token exists, let the request proceed
    return NextResponse.next()
  }
}

export const config = {
  matcher: ['/my-blogs/:path*', '/account/:path*'],
}
