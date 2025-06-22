'use client';

import React, { useState, useEffect } from 'react';
import { IoHomeOutline, IoSearchOutline, IoDocumentTextOutline, IoPersonOutline, IoLogInOutline, IoLogOutOutline } from 'react-icons/io5';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

const menuItems = [
	{ title: 'Home', icon: <IoHomeOutline />, gradientFrom: '#4ECDC4', gradientTo: '#44A08D', href: '/' },
	{ title: 'Search', icon: <IoSearchOutline />, gradientFrom: '#56CCF2', gradientTo: '#2F80ED', href: '/search' },
	{ title: 'My Blogs', icon: <IoDocumentTextOutline />, gradientFrom: '#A8E6CF', gradientTo: '#3EADCF', href: '/my-blogs' },
];

export default function Navbar() {
	const [isAuthenticated, setIsAuthenticated] = useState(false);
	const router = useRouter();

	useEffect(() => {
		const token = Cookies.get('access_token');
		setIsAuthenticated(!!token);
	}, []);

	const handleLogout = () => {
		Cookies.remove('access_token');
		Cookies.remove('refresh_token');
		setIsAuthenticated(false);
		router.push('/auth');
	};

	return (
		<nav className="fixed top-0 left-0 right-0 z-50 bg-white/10 backdrop-blur-md border-b border-white/20 shadow-lg">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div className="flex justify-between items-center h-16">
					{/* Logo */}
					<div className="flex-shrink-0">
						<h1 className="text-2xl font-bold bg-gradient-to-r text-white">
							MatchMyBlog
						</h1>
					</div>

					{/* Navigation Menu */}
					<div className="flex gap-4">
						{menuItems.map(({ title, icon, gradientFrom, gradientTo, href }, idx) => (
							<div
								key={idx}
								style={{ '--gradient-from': gradientFrom, '--gradient-to': gradientTo } as React.CSSProperties}
								className="relative w-[40px] h-[40px] bg-white shadow-md rounded-full flex items-center justify-center transition-all duration-300 hover:w-[120px] hover:shadow-lg group cursor-pointer"
								onClick={() => router.push(href)}
							>
								{/* Gradient background on hover */}
								<span className="absolute inset-0 rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] opacity-0 transition-all duration-300 group-hover:opacity-100"></span>
								{/* Blur glow */}
								<span className="absolute top-[5px] inset-x-0 h-full rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] blur-[10px] opacity-0 -z-10 transition-all duration-300 group-hover:opacity-30"></span>

								{/* Icon */}
								<span className="relative z-10 transition-all duration-300 group-hover:scale-0 delay-0">
									<span className="text-lg text-gray-600">{icon}</span>
								</span>

								{/* Title */}
								<span className="absolute text-white uppercase tracking-wide text-xs font-medium transition-all duration-300 scale-0 group-hover:scale-100 delay-100">
									{title}
								</span>
							</div>
						))}

						{/* Account/Login/Logout Buttons */}
						{isAuthenticated ? (
							<>
								{/* Account Button */}
								<div
									style={{ '--gradient-from': '#81C7D4', '--gradient-to': '#4FB3D9' } as React.CSSProperties}
									className="relative w-[40px] h-[40px] bg-white shadow-md rounded-full flex items-center justify-center transition-all duration-300 hover:w-[120px] hover:shadow-lg group cursor-pointer"
									onClick={() => router.push('/account')}
								>
									<span className="absolute inset-0 rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] opacity-0 transition-all duration-300 group-hover:opacity-100"></span>
									<span className="absolute top-[5px] inset-x-0 h-full rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] blur-[10px] opacity-0 -z-10 transition-all duration-300 group-hover:opacity-30"></span>
									<span className="relative z-10 transition-all duration-300 group-hover:scale-0 delay-0">
										<span className="text-lg text-gray-600"><IoPersonOutline /></span>
									</span>
									<span className="absolute text-white uppercase tracking-wide text-xs font-medium transition-all duration-300 scale-0 group-hover:scale-100 delay-100">
										Account
									</span>
								</div>
								{/* Logout Button */}
								<div
									style={{ '--gradient-from': '#f85032', '--gradient-to': '#e73827' } as React.CSSProperties}
									className="relative w-[40px] h-[40px] bg-white shadow-md rounded-full flex items-center justify-center transition-all duration-300 hover:w-[120px] hover:shadow-lg group cursor-pointer"
									onClick={handleLogout}
								>
									<span className="absolute inset-0 rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] opacity-0 transition-all duration-300 group-hover:opacity-100"></span>
									<span className="absolute top-[5px] inset-x-0 h-full rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] blur-[10px] opacity-0 -z-10 transition-all duration-300 group-hover:opacity-30"></span>
									<span className="relative z-10 transition-all duration-300 group-hover:scale-0 delay-0">
										<span className="text-lg text-gray-600"><IoLogOutOutline /></span>
									</span>
									<span className="absolute text-white uppercase tracking-wide text-xs font-medium transition-all duration-300 scale-0 group-hover:scale-100 delay-100">
										Logout
									</span>
								</div>
							</>
						) : (
							// Login Button
							<div
								style={{ '--gradient-from': '#81C7D4', '--gradient-to': '#4FB3D9' } as React.CSSProperties}
								className="relative w-[40px] h-[40px] bg-white shadow-md rounded-full flex items-center justify-center transition-all duration-300 hover:w-[120px] hover:shadow-lg group cursor-pointer"
								onClick={() => router.push('/auth')}
							>
								<span className="absolute inset-0 rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] opacity-0 transition-all duration-300 group-hover:opacity-100"></span>
								<span className="absolute top-[5px] inset-x-0 h-full rounded-full bg-[linear-gradient(45deg,var(--gradient-from),var(--gradient-to))] blur-[10px] opacity-0 -z-10 transition-all duration-300 group-hover:opacity-30"></span>
								<span className="relative z-10 transition-all duration-300 group-hover:scale-0 delay-0">
									<span className="text-lg text-gray-600"><IoLogInOutline /></span>
								</span>
								<span className="absolute text-white uppercase tracking-wide text-xs font-medium transition-all duration-300 scale-0 group-hover:scale-100 delay-100">
									Login
								</span>
							</div>
						)}
					</div>
				</div>
			</div>
		</nav>
	);
}
