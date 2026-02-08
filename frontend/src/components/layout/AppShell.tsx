/**
 * AppShell — Sticky top navbar + Chakra Drawer hamburger menu for mobile.
 */

import {
  Box,
  Flex,
  HStack,
  IconButton,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerBody,
  VStack,
  useDisclosure,
  useColorMode,
  useColorModeValue,
} from '@chakra-ui/react';
import { Link } from 'react-router-dom';
import {
  Menu,
  BarChart3,
  FileText,
  FlaskConical,
  TrendingUp,
  Home,
  Sun,
  Moon,
} from 'lucide-react';
import NavLink from './NavLink';
import type { ReactNode } from 'react';

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: <Home size={16} /> },
  { to: '/analyze', label: 'Analyze', icon: <BarChart3 size={16} /> },
  { to: '/ded', label: 'DED', icon: <FileText size={16} /> },
  { to: '/scenarios', label: 'Scenarios', icon: <FlaskConical size={16} /> },
  { to: '/compare', label: 'Compare', icon: <TrendingUp size={16} /> },
];

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { colorMode, toggleColorMode } = useColorMode();

  const navBg = useColorModeValue('white', 'gray.800');
  const navBorder = useColorModeValue('gray.200', 'gray.700');
  const logoColor = useColorModeValue('brand.600', 'brand.500');

  return (
    <>
      {/* Sticky top navbar */}
      <Box
        as="nav"
        position="sticky"
        top={0}
        zIndex="sticky"
        bg={navBg}
        borderBottom="1px"
        borderColor={navBorder}
        px={{ base: 4, md: 6 }}
        py={3}
      >
        <Flex align="center" justify="space-between">
          {/* Logo */}
          <Link to="/">
            <Box fontWeight="bold" fontSize="lg" color={logoColor}>
              PI Strategist
            </Box>
          </Link>

          {/* Desktop nav links + dark mode toggle */}
          <HStack spacing={1} display={{ base: 'none', md: 'flex' }}>
            {NAV_ITEMS.filter((n) => n.to !== '/').map((item) => (
              <NavLink key={item.to} to={item.to} icon={item.icon}>
                {item.label}
              </NavLink>
            ))}
            <IconButton
              aria-label="Toggle color mode"
              icon={colorMode === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              variant="ghost"
              size="sm"
              onClick={toggleColorMode}
            />
          </HStack>

          {/* Mobile hamburger */}
          <HStack display={{ base: 'flex', md: 'none' }}>
            <IconButton
              aria-label="Toggle color mode"
              icon={colorMode === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              variant="ghost"
              size="sm"
              onClick={toggleColorMode}
            />
            <IconButton
              aria-label="Open menu"
              icon={<Menu size={20} />}
              variant="ghost"
              onClick={onOpen}
            />
          </HStack>
        </Flex>
      </Box>

      {/* Mobile drawer */}
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent bg={navBg}>
          <DrawerCloseButton />
          <DrawerBody pt={12}>
            <VStack align="stretch" spacing={1}>
              {NAV_ITEMS.map((item) => (
                <NavLink key={item.to} to={item.to} icon={item.icon} onClick={onClose}>
                  {item.label}
                </NavLink>
              ))}
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>

      {/* Page content — full width */}
      {children}
    </>
  );
}
