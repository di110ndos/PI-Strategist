/**
 * Shared nav link with active route highlighting.
 */

import { Box } from '@chakra-ui/react';
import { Link, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

interface NavLinkProps {
  to: string;
  children: ReactNode;
  icon?: ReactNode;
  onClick?: () => void;
}

export default function NavLink({ to, children, icon, onClick }: NavLinkProps) {
  const { pathname } = useLocation();
  const isActive = pathname === to || (to !== '/' && pathname.startsWith(to));

  return (
    <Link to={to} onClick={onClick}>
      <Box
        display="flex"
        alignItems="center"
        gap={2}
        px={3}
        py={2}
        borderRadius="md"
        fontWeight={isActive ? 'semibold' : 'normal'}
        color={isActive ? 'brand.500' : 'gray.300'}
        bg={isActive ? 'whiteAlpha.100' : 'transparent'}
        _hover={{ color: 'brand.400', bg: 'whiteAlpha.50' }}
        transition="all 0.15s"
      >
        {icon}
        {children}
      </Box>
    </Link>
  );
}
