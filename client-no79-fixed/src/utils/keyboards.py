from typing import Optional
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from src.utils.callbackdata import UserMenuCallback, AdminMenuCallback

def user_builder(
    details: Optional[dict[str, str | dict[str, str | int]]] = None,
    row: int | list[int] | tuple[int, ...] = (1,),
    footer_details: Optional[dict[str, str | dict[str, str | int]]] = None
):
    builder = InlineKeyboardBuilder()

    if details:
        for text, data in details.items():
            if isinstance(data, dict):
                builder.button(
                    text=text,
                    callback_data=UserMenuCallback(**data).pack()
                )
            else:
                builder.button(
                    text=text,
                    callback_data=UserMenuCallback(section=data).pack()
                )

    # Content rows
    if isinstance(row, (list, tuple)):
        builder.adjust(*row)
    else:
        builder.adjust(row)
        
    # Footer buttons (always new row)
    if footer_details:
        for text, data in footer_details.items():
            if isinstance(data, dict):
                builder.row(InlineKeyboardButton(
                    text=text,
                    callback_data=UserMenuCallback(**data).pack()
                ))
            else:
                builder.row(InlineKeyboardButton(
                    text=text,
                    callback_data=UserMenuCallback(section=data).pack()
                ))
    
    return builder.as_markup()

def admin_builder(
    details: Optional[dict[str, str | dict[str, str | int]]] = None,
    row: int | list[int] | tuple[int, ...] = (1,),
    footer_details: Optional[dict[str, str | dict[str, str | int]]] = None
):
    builder = InlineKeyboardBuilder()

    if details:
        for text, data in details.items():
            if isinstance(data, dict):
                builder.button(
                    text=text,
                    callback_data=AdminMenuCallback(**data).pack()
                )
            else:
                builder.button(
                    text=text,
                    callback_data=AdminMenuCallback(section=data).pack()
                )

    # Content rows
    if isinstance(row, (list, tuple)):
        builder.adjust(*row)
    else:
        builder.adjust(row)
        
    # Footer buttons
    if footer_details:
        for text, data in footer_details.items():
             if isinstance(data, dict):
                builder.row(InlineKeyboardButton(
                    text=text,
                    callback_data=AdminMenuCallback(**data).pack()
                ))
             else:
                builder.row(InlineKeyboardButton(
                    text=text,
                    callback_data=AdminMenuCallback(section=data).pack()
                ))

    return builder.as_markup()