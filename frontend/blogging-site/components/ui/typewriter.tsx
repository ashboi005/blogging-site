'use client'

import React, { useState, useEffect } from 'react'

interface TypewriterProps {
  text: string[]
  speed?: number
  deleteSpeed?: number
  waitTime?: number
  className?: string
  cursorChar?: string
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  speed = 100,
  deleteSpeed = 50,
  waitTime = 2000,
  className = '',
  cursorChar = '|'
}) => {
  const [currentText, setCurrentText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showCursor, setShowCursor] = useState(true)

  useEffect(() => {
    const timeout = setTimeout(() => {
      const current = text[currentIndex]
      
      if (isDeleting) {
        setCurrentText(prev => prev.slice(0, -1))
        
        if (currentText === '') {
          setIsDeleting(false)
          setCurrentIndex(prev => (prev + 1) % text.length)
        }
      } else {
        setCurrentText(current.slice(0, currentText.length + 1))
        
        if (currentText === current) {
          setTimeout(() => setIsDeleting(true), waitTime)
        }
      }
    }, isDeleting ? deleteSpeed : speed)

    return () => clearTimeout(timeout)
  }, [currentText, currentIndex, isDeleting, text, speed, deleteSpeed, waitTime])

  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor(prev => !prev)
    }, 500)

    return () => clearInterval(cursorInterval)
  }, [])

  return (
    <span className={className}>
      {currentText}
      <span className={`${showCursor ? 'opacity-100' : 'opacity-0'} transition-opacity duration-75`}>
        {cursorChar}
      </span>
    </span>
  )
}
