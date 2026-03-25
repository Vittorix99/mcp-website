"use client"

import Link from "next/link"
import Image from "next/image"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard, Calendar, Receipt, CreditCard,
  Inbox, Images, Zap, SlidersHorizontal,
  Users, Megaphone, UserCheck, Bug,
  ChevronRight, LogOut,
} from "lucide-react"
import "@/app/style/admin.css"

import { routes } from "@/config/routes"
import { logout } from "@/config/firebase"
import { useUser } from "@/contexts/userContext"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar"

const navigationSections = [
  {
    title: "Generale",
    items: [
      { title: "Dashboard",   url: routes.admin.dashboard,    icon: LayoutDashboard },
    ],
  },
  {
    title: "Gestione",
    items: [
      { title: "Eventi",      url: routes.admin.events,       icon: Calendar  },
      { title: "Acquisti",    url: routes.admin.purchases,    icon: Receipt   },
      { title: "Tessere",     url: routes.admin.memberships,  icon: CreditCard },
      { title: "Foto Eventi", url: routes.admin.eventsPhotos, icon: Images    },
    ],
  },
  {
    title: "Comunicazioni",
    items: [
      { title: "Messaggi", url: routes.admin.messages, icon: Inbox },
      {
        title: "Sender",
        url: routes.admin.sender.campaigns,
        icon: Zap,
        children: [
          { title: "Campagne",   url: routes.admin.sender.campaigns,   icon: Megaphone },
          { title: "CRM",        url: routes.admin.sender.subscribers, icon: Users     },
          { title: "Opt In/Out", url: routes.admin.sender.optinOptout, icon: UserCheck },
        ],
      },
    ],
  },
  {
    title: "Impostazioni",
    items: [
      { title: "Settings",   url: routes.admin.settings,  icon: SlidersHorizontal },
      { title: "Error Logs", url: routes.admin.errorLogs, icon: Bug               },
    ],
  },
]

function NavIcon({ Icon, active }) {
  return (
    <span
      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md transition-all duration-150 ${
        active
          ? "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/25"
          : "bg-white/[0.06] text-neutral-500"
      }`}
    >
      <Icon className="h-[15px] w-[15px]" />
    </span>
  )
}

function UserAvatar({ email }) {
  const initials = email ? email.slice(0, 2).toUpperCase() : "AD"
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orange-500/15 ring-1 ring-orange-500/30 text-orange-400 text-xs font-bold tracking-wide">
      {initials}
    </div>
  )
}

export function CustomSidebar() {
  const pathname = usePathname()
  const { user } = useUser()

  const isActive = (url) =>
    url !== routes.admin.dashboard
      ? pathname.startsWith(url)
      : pathname === url

  return (
    <Sidebar className="border-r border-orange-500/15 custom-sidebar flex flex-col">

      {/* ─── Header ─── */}
      <SidebarHeader className="admin-header px-4 pt-5 pb-4">
        <Link href={routes.home} className="inline-flex items-center group">
          <Image
            src="/secondaryLogoWhite.png"
            alt="MCP Logo"
            width={72}
            height={50}
            className="w-[60px] h-auto shrink-0 transition-all duration-200 group-hover:opacity-70"
            priority
          />
        </Link>
        <div className="mt-4 h-px bg-gradient-to-r from-white/10 via-white/5 to-transparent" />
      </SidebarHeader>

      {/* ─── Navigation ─── */}
      <SidebarContent className="custom-sidebar flex-1 overflow-y-auto px-2.5 py-3">
        {navigationSections.map((section) => (
          <div key={section.title} className="mb-5">

            {/* Section label */}
            <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-600">
              {section.title}
            </p>

            <SidebarMenu className="space-y-0.5">
              {section.items.map((item) => {
                const active   = isActive(item.url)
                const hasChildren = item.children?.length > 0
                const childActive = hasChildren && item.children.some((c) => isActive(c.url))
                const isHighlighted = (active && !hasChildren) || childActive
                const expanded = active || childActive

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={active && !hasChildren}
                      tooltip={item.title}
                      className={`group h-10 rounded-lg px-0 transition-all duration-150 ${
                        isHighlighted
                          ? "bg-white/[0.05]"
                          : "hover:bg-white/[0.04]"
                      }`}
                    >
                      <Link href={item.url} className="flex items-center w-full gap-3 px-2">
                        <NavIcon Icon={item.icon} active={isHighlighted} />

                        <span className={`flex-1 text-[13px] font-medium transition-colors duration-150 ${
                          isHighlighted
                            ? "text-white"
                            : "text-neutral-400 group-hover:text-neutral-200"
                        }`}>
                          {item.title}
                        </span>

                        {hasChildren && (
                          <ChevronRight
                            className={`h-3.5 w-3.5 shrink-0 text-neutral-600 transition-transform duration-200 ${
                              expanded ? "rotate-90" : ""
                            }`}
                          />
                        )}
                      </Link>
                    </SidebarMenuButton>

                    {/* ── Sub-items ── */}
                    {hasChildren && expanded && (
                      <div className="ml-[22px] mt-0.5 space-y-0.5 border-l border-white/[0.07] pl-4">
                        {item.children.map((child) => {
                          const childIsActive = isActive(child.url)
                          return (
                            <Link
                              key={child.title}
                              href={child.url}
                              className={`group flex items-center gap-2.5 rounded-md px-2 py-[7px] transition-all duration-150 ${
                                childIsActive
                                  ? "text-orange-400"
                                  : "text-neutral-500 hover:text-neutral-200"
                              }`}
                            >
                              <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded transition-all duration-150 ${
                                childIsActive
                                  ? "text-orange-400"
                                  : "text-neutral-600 group-hover:text-neutral-300"
                              }`}>
                                <child.icon className="h-[13px] w-[13px]" />
                              </span>
                              <span className="text-[12.5px] font-medium">{child.title}</span>
                              {childIsActive && (
                                <span className="ml-auto h-1 w-1 rounded-full bg-orange-500" />
                              )}
                            </Link>
                          )
                        })}
                      </div>
                    )}
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </div>
        ))}
      </SidebarContent>

      {/* ─── Footer / User + Logout ─── */}
      <SidebarFooter className="px-2.5 pb-4 pt-1">
        <div className="h-px mb-3 bg-gradient-to-r from-white/10 via-white/5 to-transparent" />
        <div className="group flex items-center gap-3 rounded-xl bg-white/[0.04] px-3 py-2.5 ring-1 ring-white/[0.06] transition-all duration-150 hover:ring-white/10">
          <UserAvatar email={user?.email} />

          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-medium uppercase tracking-wider text-neutral-600 leading-none mb-1">
              Admin
            </p>
            <p className="text-[12px] font-medium text-neutral-400 truncate leading-none">
              {user?.email ?? "—"}
            </p>
          </div>

          <button
            onClick={logout}
            title="Logout"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-neutral-600 ring-1 ring-transparent transition-all duration-150 hover:bg-red-500/10 hover:text-red-400 hover:ring-red-500/20"
          >
            <LogOut className="h-[14px] w-[14px]" />
          </button>
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
