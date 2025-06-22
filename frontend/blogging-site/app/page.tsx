'use client'

import { useState, useEffect } from 'react'
import Cookies from 'js-cookie'
import Navbar from "../components/ui/navbar";
import { Footer } from "../components/ui/footer";
import Aurora from "@/components/home/aurora";
import { BlurFade } from "@/components/home/blur-fade";
import { Typewriter } from "@/components/home/typewriter";

export default function Home() {
  const [userName, setUserName] = useState<string | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      const token = Cookies.get('access_token')
      if (token) {
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          })
          if (res.ok) {
            const data = await res.json()
            setUserName(data.first_name || data.username)
          }
        } catch (error) {
          console.error("Failed to fetch user:", error)
        }
      }
    }
    fetchUser()
  }, [])

  return (
    <div className="min-h-screen bg-black">
      <Navbar />
        <Aurora
        colorStops={["#4ECDC4","#3A29FF", "#2F80ED"]}
        blend={0.5}
        amplitude={1.2}
        speed={0.8}
        />
        <div className="flex items-center justify-center min-h-[60vh] flex-col space-y-8">
          <BlurFade delay={0.25} inView>
            <h2 className="text-3xl text-white font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-center">
              {userName ? `Hello ${userName} 👋` : 'Hello There! 👋'}
            </h2>
          </BlurFade>
          
          <BlurFade delay={0.5} inView>
            <div className="text-2xl sm:text-3xl xl:text-4xl text-center text-white font-medium">
              <span>{"Read & Write about "}</span>
              <Typewriter
                text={[
                  "Cutting-edge Technology",
                  "Elegant Programming",
                  "Innovative Web Development",
                  "Fascinating Data Science",
                  "Revolutionary Machine Learning",
                  "Groundbreaking Artificial Intelligence",
                  "Meaningful Life Experiences",
                  "Captivating Fictional Stories",
                  "Strategic Business Insights",
                  "Inspiring Startup Journeys",
                  "Creative Marketing Strategies",
                  "Stunning Creative Design",
                  "Mindful Lifestyle",
                  "Holistic Health & Wellness",
                  "Adventurous Travel Experiences",
                  "Delicious Food & Culture",
                  "Transformative Education"
                ]}
                speed={70}
                className="text-yellow-500"
                waitTime={1500}
                deleteSpeed={40}
                cursorChar={"_"}
              />
            </div>
          </BlurFade>
        </div>
      <Footer />
    </div>
  );
}
